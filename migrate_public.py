import sqlite3
import database

def migrate():
    conn = database.get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute("ALTER TABLE attendance ADD COLUMN full_name TEXT")
        print("Added full_name column.")
    except sqlite3.OperationalError:
        print("full_name column already exists.")
        
    try:
        c.execute("ALTER TABLE attendance ADD COLUMN roll_no TEXT")
        print("Added roll_no column.")
    except sqlite3.OperationalError:
        print("roll_no column already exists.")

    try:
        c.execute("ALTER TABLE attendance ADD COLUMN device_id TEXT")
        print("Added device_id column.")
    except sqlite3.OperationalError:
        print("device_id column already exists.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
