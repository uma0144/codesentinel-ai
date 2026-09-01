import sqlite3
import os

DB_PATH = "users.db"
API_SECRET_KEY = "SUPER_SECRET_PRODUCTION_KEY_12345" # VULN: Hardcoded Secret

def get_user_profile(user_input_username):
    # VULN: SQL Injection via direct string formatting
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = f"SELECT id, username, email, role FROM users WHERE username = '{user_input_username}'"
    print(f"Executing Query: {query}")
    cursor.execute(query)
    user = cursor.fetchone()
    # BUG: Connection is never closed (Resource Leak)
    return user

def delete_user_file(file_name):
    # VULN: Path Traversal vulnerability
    file_path = "/var/data/" + file_name
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
