import psycopg2
from psycopg2 import sql

class Database:
    def __init__(self, **kwargs):
        self.connection = psycopg2.connect(
            host=kwargs.get("host"),
            port=kwargs.get("port"),
            dbname=kwargs.get("dbname"),
            user=kwargs.get("user"),
            password=kwargs.get("password")
        )
        self.cursor = self.connection.cursor()
    
    def create_table(self, table_name, columns):
        column_defs = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
        create_table_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
            sql.Identifier(table_name),
            sql.SQL(column_defs)
        )
        try:
            self.cursor.execute(create_table_query)
            self.connection.commit()
        except Exception as e:
            self.rollback()
            print("Error creating table:", e)

    def insert(self, table_name, **data):
        columns = data.keys()
        values = tuple(data.values())
        
        insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(", ").join(sql.Placeholder() * len(values))
        )
        try:
            self.cursor.execute(insert_query, values)
            self.connection.commit()
        except Exception as e:
            self.rollback()
            print("Error inserting data:", e)

    def read(self, table_name, columns="*", conditions=None, limit=None):
        if isinstance(columns, list):
            columns = sql.SQL(", ").join(map(sql.Identifier, columns))
        else:
            columns = sql.SQL(columns)
        
        query = sql.SQL("SELECT {} FROM {}").format(columns, sql.Identifier(table_name))
        
        if conditions:
            where_clause = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(
                sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder(k)]) for k in conditions.keys()
            )
            query += where_clause
            
        if limit:
            query += sql.SQL(" LIMIT {}").format(sql.Literal(limit))
        
        try:
            self.cursor.execute(query, conditions)
            return self.cursor.fetchall()
        except Exception as e:
            print("Error reading data:", e)
            self.rollback()  # Roll back to reset the transaction state
            return []

    def update(self, table_name, updates, conditions):
        set_clause = sql.SQL(", ").join(
            sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder(f"set_{k}")]) for k in updates.keys()
        )
        where_clause = sql.SQL(" AND ").join(
            sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder(f"where_{k}")]) for k in conditions.keys()
        )
        
        update_query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
            sql.Identifier(table_name), set_clause, where_clause
        )
        
        try:
            params = {f"set_{k}": v for k, v in updates.items()}
            params.update({f"where_{k}": v for k, v in conditions.items()})
            self.cursor.execute(update_query, params)
            self.connection.commit()
        except Exception as e:
            self.rollback()
            print("Error updating data:", e)

    def delete(self, table_name, conditions):
        where_clause = sql.SQL(" AND ").join(
            sql.Composed([sql.Identifier(k), sql.SQL(" = "), sql.Placeholder(k)]) for k in conditions.keys()
        )
        
        delete_query = sql.SQL("DELETE FROM {} WHERE {}").format(
            sql.Identifier(table_name), where_clause
        )
        try:
            self.cursor.execute(delete_query, conditions)
            self.connection.commit()
        except Exception as e:
            self.rollback()
            print("Error deleting data:", e)

    def rollback(self):
        self.connection.rollback()
    
    def close(self):
        self.cursor.close()
        self.connection.close()
