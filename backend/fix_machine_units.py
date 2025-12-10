import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join("backend", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found.")
    sys.exit(1)

# Handle Render's postgres:// URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Machines data - Unit 2 (11 machines)
UNIT2_MACHINES = [
    "Gas Cutting",
    "Tig Welding",
    "CO2 Welding LD",
    "CO2 Welding HD",
    "PSG",
    "Ace Superjobber",
    "Slotting Machine",
    "Surface Grinding",
    "Thakur Drilling",
    "Toolvasor Magnetic Drilling",
    "EIFCO Radial Drilling",
]

# Machines data - Unit 1 (28 machines)
UNIT1_MACHINES = [
    "Hand Grinder",
    "Bench Grinder",
    "Tool and Cutter Grinder",
    "Turnmaster",
    "Leader",
    "Bandsaw cutting Manual",
    "Bandsaw cutting Auto",
    "VMC Pilot",
    "ESTEEM DRO",
    "FW Horizontal",
    "Arno",
    "BFW No 2",
    "Engraving Machine",
    "Delapena Honing Machine",
    "Bench Grinder 2",
    "Buffing Machine",
    "Tooth Rounding Machine",
    "Lapping Machine",
    "Hand Drilling 2",
    "Hand Drilling 1",
    "Hand Grinding 2",
    "Hand Grinding 1",
    "Hitachi Cutting Machine",
    "HMT Rack Cutting",
    "L Rack Cutting",
    "Reinecker",
    "Zimberman",
    "EIFCO Stationary Drilling",
]

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("🔧 Fixing Machine Unit Assignments...")
    
    # Fix Unit 1 Machines
    for name in UNIT1_MACHINES:
        cursor.execute("UPDATE machines SET unit_id = 1 WHERE name = %s", (name,))
    
    # Fix Unit 2 Machines
    for name in UNIT2_MACHINES:
        cursor.execute("UPDATE machines SET unit_id = 2 WHERE name = %s", (name,))
        
    conn.commit()
    print("✅ Machine units updated successfully!")
    
    # Verify
    cursor.execute("SELECT unit_id, count(*) FROM machines GROUP BY unit_id")
    counts = cursor.fetchall()
    print("\n📊 New Machine Counts per Unit:")
    for unit_id, count in counts:
        print(f"   Unit {unit_id}: {count} machines")
        
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
