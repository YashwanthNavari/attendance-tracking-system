import sqlite3
import database
import sys

def inspect():
    conn = database.get_db_connection()
    c = conn.cursor()
    
    with open('schema_info.txt', 'w') as f:
        f.write("--- SESSIONS Table Info ---\n")
        try:
            columns = c.execute("PRAGMA table_info(sessions)").fetchall()
            for col in columns:
                f.write(f"{dict(col)}\n")
        except Exception as e:
            f.write(f"Error reading sessions table: {e}\n")

        f.write("\n--- ATTENDANCE Table Info ---\n")
        try:
            columns = c.execute("PRAGMA table_info(attendance)").fetchall()
            for col in columns:
                f.write(f"{dict(col)}\n")
        except Exception as e:
            f.write(f"Error reading attendance table: {e}\n")

    conn.close()
    print("Schema info written to schema_info.txt")

if __name__ == "__main__":
    inspect()
