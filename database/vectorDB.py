import psycopg2
from openai import OpenAI
import uuid
from psycopg2 import sql
import os
import voyageai

voyage_api = os.getenv('VOYAGE_API')
vo = voyageai.Client(api_key='pa-8VuCjYTvgxSqIw33ADELwZUxCyV3Cz7mBLVy9RovGrY')

distance_dict = {
    'L2' : '<->',
    'inner': '<#>',
    'cosine': '<=>',
    'L1': '<=>',
    'hamming': '<~>',
    'jaccard': '<%>'
}  

class VectorDB:
    def __init__(self, **kwargs):

        # Initialize PostgreSQL connection with kwargs
        self.connection = psycopg2.connect(
            host=kwargs.get("host"),
            port=kwargs.get("port"),
            dbname=kwargs.get("dbname"),
            user=kwargs.get("user"),
            password=kwargs.get("password")
        )
        self.cursor = self.connection.cursor()
        openai_api = kwargs.get("openai_api_key")
        self.client = OpenAI(api_key=openai_api)
    
    def create_table(self, table_name: str, **kwargs):
        # Construct table creation SQL based on provided columns
        columns = kwargs.get("columns")
        
        column_defs = []
        
        for col, dtype in columns.items():
            if "FOREIGN KEY" in dtype:
                data_type, fk_reference = dtype.split(", FOREIGN KEY ")
                fk_reference = fk_reference.strip()  # Remove any leading/trailing spaces
                column_def = f"{col} {data_type} {fk_reference}"
            else:
                column_def = f"{col} {dtype}"
            
            column_defs.append(column_def)
        
        column_defs_sql = ", ".join(column_defs)
        
        # Create the SQL query for table creation
        create_table_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
            sql.Identifier(table_name),
            sql.SQL(column_defs_sql)
        )
        
        try:
            self.cursor.execute(create_table_query)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print(f"Error creating table {table_name}:", e)
    
    def rollback(self):
        # Rollback transaction in case of errors
        self.connection.rollback()
    
    def get_embedding(self, texts, model="text-embedding-3-small"):
        texts =[text.replace("\n", " ") for text in texts]
        return self.client.embeddings.create(input = texts, model=model).data[0].embedding
    
    def insert_embedding(self, **kwargs):

        table_name = kwargs.pop("table_name")

        if "embedding" not in kwargs:
            raise ValueError("Embedding data must be provided in 'kwargs' with the key 'embedding'")

        unique_id = str(uuid.uuid4())
        kwargs["id"] = unique_id

        # Prepare columns and values for dynamic insertion
        additional_columns = {key: value for key, value in kwargs.items() if key != "table_name"}
        column_names = list(additional_columns.keys())
        column_values = list(additional_columns.values())

        # Generate the placeholders for the values (%s for each value)
        placeholders = ", ".join(["%s"] * len(column_values))

        # Construct the SQL query dynamically
        try:
            query = f"""
                INSERT INTO {table_name} ({", ".join(column_names)})
                VALUES ({placeholders});
            """
            self.cursor.execute(query, column_values)
            self.connection.commit()
        except Exception as e:
            print("Error inserting embedding:", e)
            self.rollback()

    def query_with_distance(self, query_texts: list, distance: str = 'L2', **kwargs):
        table_name = kwargs.get("table_name")
        limit = kwargs.get("limit", 5)
        selected_columns = kwargs.get("columns", ["id", "reportId", "text"]) 
        # Get multiple where clauses from kwargs
        where_clauses = kwargs.get("where_clauses", [])
        
        # Combine where clauses with 'AND' or 'OR'
        if where_clauses:
            where_clause = " AND ".join(where_clauses)  # Combine with AND, change to OR if needed

        try:
            # Generate the query embedding using the embedder
            query_embeddings = get_embedding_voyage(texts=query_texts, client=vo)
            res = []
            for query_embedding in query_embeddings:
                try:
                    embedding_str = f"ARRAY{query_embedding}::vector"
                    
                    # Construct the SQL query to fetch results with similarity distance
                    column_str = ", ".join(selected_columns)  
                    query = f"""
                        SELECT {column_str}, embedding {distance_dict[distance]} {embedding_str} AS distance
                        FROM "{table_name}"
                        WHERE {where_clause}
                        ORDER BY distance
                        LIMIT {limit};
                    """
                    self.cursor.execute(query)
                    results = self.cursor.fetchall()

                    res.append([
                    {column: value for column, value in zip(selected_columns + ["distance"], row)}
                    for row in results
                    ])
                except Exception as e:
                    res.append([None])
                    raise e                  

            # Return results with column names and distance
            return res
        
        except Exception as e:
            print("Error querying with distance:", e)
            
            self.rollback()
            
            return []
    
    
    def execute(self, query, params=None):
        """Execute any SQL command."""
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except Exception as e:
            self.rollback()
            print("Error executing query:", e)

    def query_with_distance_rag(self, query_texts: list|str, distance: str = 'L2', **kwargs):
        table_name = kwargs.get("table_name")
        limit = kwargs.get("limit", 5)
        selected_columns = kwargs.get("columns", ["id", "reportId", "text"]) 
        # Get multiple where clauses from kwargs
        where_clauses = kwargs.get("where_clauses", [])
        
        # Combine where clauses with 'AND' or 'OR'
        if where_clauses:
            where_clause = " AND ".join(where_clauses)  # Combine with AND, change to OR if needed
        else:
            where_clause = "1=1"  # No condition, selects all

        try:
            # Generate the query embedding using the embedder
            query_embeddings = get_embedding_openai(texts=query_texts, model=self.client)
            res = []
            for query_embedding in query_embeddings:
                embedding_str = f"ARRAY{query_embedding}::vector"
                
                # Construct the SQL query to fetch results with similarity distance
                column_str = ", ".join(selected_columns)  
                query = f"""
                    SELECT {column_str}, embedding {distance_dict[distance]} {embedding_str} AS distance
                    FROM "{table_name}"
                    WHERE {where_clause}
                    ORDER BY distance
                    LIMIT {limit};
                """
                self.cursor.execute(query)
                results = self.cursor.fetchall()

                res.append([
                {column: value for column, value in zip(selected_columns + ["distance"], row)}
                for row in results
                ])

            # Return results with column names and distance
            return res
        
        except Exception as e:
            print("Error querying with distance:", e)
            self.rollback()
            return []
    
    
    def execute(self, query, params=None):
        """Execute any SQL command."""
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except Exception as e:
            self.rollback()
            print("Error executing query:", e)

    
    def close(self):
        # Close the database connection
        self.cursor.close()
        self.connection.close()

def get_embedding_voyage(texts, client: voyageai.Client):
    
    embeddings = client.embed(texts, model="voyage-finance-2", input_type="document")
    embeddings = embeddings.embeddings

    return embeddings

def get_embedding_openai(texts, model: OpenAI):
    response = model.embeddings.create(
    input=texts,
    model="text-embedding-3-large"
    )

    return [response.data[0].embedding]