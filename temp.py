import sqlite3
import pandas as pd

# Path to your SQLite database
db_path = "/Users/suraj/Downloads/StyleNest.db"

# Connect to the database
conn = sqlite3.connect(db_path)

# Fetch and print all table names
tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
print("Tables in database:\n", tables)

# Display first few rows from each table
for table_name in tables['name']:
    print(f"\nPreview of table: {table_name}")
    df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5;", conn)
    print(df)

# Close connection
conn.close()
