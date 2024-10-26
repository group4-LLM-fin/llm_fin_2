import psycopg2
import openai
import uuid

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
        openai.api_key = kwargs.get("openai_api_key")
    
    def create_table(self, table_name: str, **kwargs):
        # Construct table creation SQL based on provided columns
        columns = kwargs.get("columns")
        
        column_definitions = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
        
        try:
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions});"
            self.cursor.execute(create_table_query)
            self.connection.commit()
        except Exception as e:
            raise e
    
    def rollback(self):
        # Rollback transaction in case of errors
        self.connection.rollback()
    
    def get_openai_embedding(self, text, **kwargs):
        # Get embedding from OpenAI with customizable model
        model = kwargs.get("model", "text-embedding-ada-002")
        response = openai.Embedding.create(input=text, model=model)
        return response['data'][0]['embedding']
    
    def insert_embedding(self, **kwargs):

        table_name = kwargs.pop("table_name")

        if "Embedding" not in kwargs:
            raise ValueError("Embedding data must be provided in 'kwargs' with the key 'Embedding'")

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
    
    def query_with_distance(self, query_text, embedder, distance: str = 'L2', **kwargs):
        table_name = kwargs.get("table_name", "accounts")
        limit = kwargs.get("limit", 5)
        selected_columns = kwargs.get("columns", ["id", "reportId", "text"]) 

        try:
            # Generate the query embedding using the embedder
            query_embedding = embedder.embed_documents(texts=[query_text])[0]
            embedding_str = f"ARRAY{query_embedding}::vector"

            # Construct the SQL query to fetch results with similarity distance
            column_str = ", ".join(selected_columns)  
            query = f"""
                SELECT {column_str}, embedding {distance_dict[distance]} {embedding_str} AS distance
                FROM {table_name}
                ORDER BY distance
                LIMIT {limit};
            """
            
            self.cursor.execute(query)
            results = self.cursor.fetchall()

            # Return results with column names and distance
            return [
                {column: value for column, value in zip(selected_columns + ["distance"], row)}
                for row in results
            ]

        except Exception as e:
            print("Error querying with distance:", e)
            self.rollback()
            return []
        
        except Exception as e:
            print("Error querying with distance:", e)
            self.rollback()
            return []
    
    def close(self):
        # Close the database connection
        self.cursor.close()
        self.connection.close()
