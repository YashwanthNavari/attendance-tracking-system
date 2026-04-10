import database
import sqlite3
import sys

def add_user(username, password, role, full_name):
    conn = database.get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
            (username, password, role, full_name)
        )
        conn.commit()
        print(f"User '{username}' added successfully.")
    except sqlite3.IntegrityError:
        print(f"Error: User '{username}' already exists.")
    except Exception as e:
        print(f"Error adding user: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python add_user.py <username> <password> <role> <full_name>")
    else:
        add_user(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
