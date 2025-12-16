from app.core.init_data import init_db_data
import sys

def test_startup():
    print("Testing startup initialization logic...")
    try:
        init_db_data()
        print("✅ Startup initialization completed without errors.")
    except Exception as e:
        print(f"❌ Startup initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_startup()
