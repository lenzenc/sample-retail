def init_db():
    # Delete existing database file if it exists
    if os.path.exists(DATABASE_URL):
        os.remove(DATABASE_URL)

    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # Add this line here
    
    # Define the base path for SQL files
    sql_base_path = "./api/sql"
    
    # List of SQL files to execute in order
    sql_files = ["items.sql", "orders.sql", "data.sql"]
    
    try:
        for sql_file in sql_files:
            file_path = os.path.join(sql_base_path, sql_file)
            print(f"Loading... {file_path}")
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    sql_script = f.read()
                    conn.executescript(sql_script)
            else:
                print(f"Warning: SQL file not found: {file_path}")
                
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise
    finally:
        conn.close()