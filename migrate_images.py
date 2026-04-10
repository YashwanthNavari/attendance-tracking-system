import sqlite3
import database

def migrate():
    conn = database.get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute("ALTER TABLE attendance ADD COLUMN captured_image_path TEXT")
        print("Added captured_image_path column.")
    except sqlite3.OperationalError:
        print("captured_image_path column already exists.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
