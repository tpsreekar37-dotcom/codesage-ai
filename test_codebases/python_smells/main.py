import sqlite3

def get_user_data(username):
    # SQL injection vulnerability
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE name = '{username}'"
    cursor.execute(query)
    return cursor.fetchall()

def execute_untrusted(user_code):
    # Remote code execution risk
    eval(user_code)

def read_log_file():
    # Resource leak: file not closed
    f = open("app.log", "r")
    return f.read(100)