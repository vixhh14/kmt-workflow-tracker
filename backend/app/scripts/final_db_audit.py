
import sys
import os
from sqlalchemy import create_engine, inspect, text

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.config import settings

def audit_db():
    print("--- STARTING DB AUDIT ---")
    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        
        tables = ['users', 'tasks', 'machines', 'projects', 'attendance']
        
        for table in tables:
            print(f"\nTABLE: {table}")
            if not inspector.has_table(table):
                print(f"  ❌ Table {table} NOT FOUND!")
                continue
                
            columns = inspector.get_columns(table)
            for col in columns:
                print(f"  - {col['name']} ({col['type']}) | Nullable: {col['nullable']} | Default: {col.get('default')}")
            
            # Check PK
            pk = inspector.get_pk_constraint(table)
            print(f"  -> PK: {pk['constrained_columns']}")
            
            # Check FKs
            fks = inspector.get_foreign_keys(table)
            for fk in fks:
                print(f"  -> FK: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

            # Sample Data (ID types)
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table} LIMIT 3"))
                rows = result.fetchall()
                if rows:
                    print("  -> Sample IDs:", [row[0] for row in rows]) # Assuming first col is PK
                else:
                    print("  -> Table is empty.")

    except Exception as e:
        print(f"❌ AUDIT FAILED: {e}")
    print("\n--- AUDIT COMPLETE ---")

if __name__ == "__main__":
    audit_db()
