
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.sheets_db import SHEETS_SCHEMA
from app.core.sheets_client import sheets_client

load_dotenv()

def migrate():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found")
        return

    # Fix Render-style postgres:// URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print(f"🚀 Connecting to PostgreSQL and migrating to Google Sheets...")
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        for table_name, columns in SHEETS_SCHEMA.items():
            print(f"📊 Migrating table: {table_name}...")
            try:
                # 1. Read from Postgres
                result = conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = [dict(row._mapping) for row in result]
                
                if not rows:
                    print(f"  Empty table, skipping.")
                    continue
                
                # 2. Get/Create Sheet
                try:
                    sheet = sheets_client.get_sheet(table_name)
                except Exception:
                    # If not found, create it (Manual step usually, but we can try to clear and rewrite)
                    print(f"  Sheet '{table_name}' not found. Please create it manually with headers.")
                    continue

                # 3. Clear and write headers
                print(f"  Writing {len(rows)} rows...")
                sheet.clear()
                sheet.append_row(columns) # Headers
                
                # 4. Prepare data
                all_values = []
                for r in rows:
                    row_values = []
                    for col in columns:
                        val = r.get(col, "")
                        if val is None:
                            val = ""
                        elif hasattr(val, "isoformat"):
                            val = val.isoformat()
                        row_values.append(str(val))
                    all_values.append(row_values)
                
                # Batch update for speed
                if all_values:
                    sheet.append_rows(all_values)
                
                print(f"  ✅ Completed {table_name}")
            except Exception as e:
                print(f"  ❌ Error migrating {table_name}: {str(e)}")

    print("\n🎉 Migration process finished!")

if __name__ == "__main__":
    migrate()
