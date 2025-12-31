import os
from dotenv import load_dotenv
load_dotenv()
db_url = os.getenv("DATABASE_URL")
if db_url:
    print(f"DATABASE_URL is set (starts with {db_url[:15]}...)")
else:
    print("DATABASE_URL is NOT set")
