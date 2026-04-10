import database
import sqlite3
import os

def check_and_fix_users():
    if not os.path.exists(database.DB_NAME):
        print("Database not found, initializing...")
        database.init_db()
        
    conn = database.get_db_connection()
    try:
        users = conn.execute('SELECT * FROM users').fetchall()
        print(f"Found {len(users)} users.")
        for u in users:
            print(f" - {u['username']} ({u['role']})")
            
        if len(users) == 0:
            print("No users found. Creating demo users...")
            conn.execute("INSERT INTO users (username, password, role, full_name) VALUES ('faculty1', 'pass', 'faculty', 'Dr. Smith')")
            conn.execute("INSERT INTO users (username, password, role, full_name) VALUES ('student1', 'pass', 'student', 'John Doe')")
            conn.commit()
            print("Users created.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_and_fix_users()
