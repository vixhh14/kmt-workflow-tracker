
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL not found in .env")
        return

    # Mask password for safety
    masked_url = url.split("@")[-1] if "@" in url else url
    print(f"📡 Testing connection to: {masked_url}")

    try:
        print("🔄 Attempting psycopg2.connect with sslmode=require & gssencmode=disable...")
        conn = psycopg2.connect(url, sslmode='require', gssencmode='disable', connect_timeout=10)
        print("✅ SUCCESS! Connected to database.")
        
        cur = conn.cursor()
        cur.execute("SELECT version();")
        print(f"📊 Server version: {cur.fetchone()[0]}")
        
        cur.close()
        conn.close()
        print("🔌 Connection closed safely.")
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {e}")
        print("\n💡 POSSIBLE CAUSES:")
        print("1. IP NOT WHITELISTED: Go to Render Dashboard -> Database -> Settings -> Access Control and add your IP.")
        print("2. WRONG URL: Double check the 'External Database URL' in Render.")
        print("3. LOCAL NETWORK: Your ISP or Firewall might be blocking port 5432 or stripping SSL.")

if __name__ == "__main__":
    test_connection()
