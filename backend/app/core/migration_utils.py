import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.database import DEFAULT_DB_PATH, SQLALCHEMY_DATABASE_URL

def migrate_sqlite_to_postgres():
    """
    Migrates data from SQLite to PostgreSQL.
    Only runs if:
    1. We are using PostgreSQL (DATABASE_URL is set)
    2. The PostgreSQL database is empty (to prevent overwriting)
    """
    
    # 1. Check if we are using Postgres
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        print("[Migration] Using SQLite. No migration needed.")
        return

    print("[Migration] Checking if migration is needed...")
    
    # 2. Connect to Postgres
    try:
        pg_conn = psycopg2.connect(SQLALCHEMY_DATABASE_URL)
        pg_cursor = pg_conn.cursor()
        
        # Check if tables exist and are empty (checking 'users' table as a proxy)
        pg_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        users_table_exists = pg_cursor.fetchone()[0]
        
        if not users_table_exists:
            print("[Migration] Target tables do not exist yet. Skipping migration (tables will be created by SQLAlchemy).")
            pg_conn.close()
            return

        pg_cursor.execute("SELECT COUNT(*) FROM users")
        user_count = pg_cursor.fetchone()[0]
        
        if user_count > 0:
            print(f"[Migration] Target database already has {user_count} users. Skipping migration.")
            pg_conn.close()
            return
            
        print("[Migration] Target database is empty. Starting migration from SQLite...")
        
    except Exception as e:
        print(f"[Migration] Error connecting to Postgres: {e}")
        return

    # 3. Connect to SQLite
    if not os.path.exists(DEFAULT_DB_PATH):
        print(f"[Migration] Source SQLite DB not found at {DEFAULT_DB_PATH}. Skipping.")
        pg_conn.close()
        return
        
    try:
        sqlite_conn = sqlite3.connect(DEFAULT_DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        # 4. Define tables to migrate in order of dependency
        tables = [
            "units",
            "machine_categories",
            "machines",
            "users",
            "tasks",
            "subtasks",
            "task_time_logs",
            "planning_tasks",
            "outsource_items",
            "attendance",
            "user_approvals",
            "user_machines"
        ]
        
        for table in tables:
            print(f"[Migration] Migrating table: {table}...")
            
            # Get data from SQLite
            try:
                sqlite_cursor.execute(f"SELECT * FROM {table}")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    print(f"   - No data in {table}")
                    continue
                    
                # Get column names
                columns = rows[0].keys()
                cols_str = ", ".join(columns)
                placeholders = ", ".join(["%s"] * len(columns))
                
                # Insert into Postgres
                success_count = 0
                for row in rows:
                    values = tuple(row)
                    try:
                        query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                        pg_cursor.execute(query, values)
                        success_count += 1
                    except Exception as row_err:
                        print(f"   - Failed to insert row in {table}: {row_err}")
                        pg_conn.rollback() # Rollback the failed row insert
                        continue
                
                pg_conn.commit()
                print(f"   - Migrated {success_count} records for {table}")
                
            except Exception as table_err:
                print(f"   - Error migrating table {table}: {table_err}")
                
        print("[Migration] Migration completed successfully!")
        
    except Exception as e:
        print(f"[Migration] Critical error during migration: {e}")
    finally:
        if sqlite_conn:
            sqlite_conn.close()
        if pg_conn:
            pg_conn.close()
