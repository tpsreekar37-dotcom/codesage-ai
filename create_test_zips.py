import os
import zipfile

test_dir = r"C:\Users\tpvij\Desktop\Google_AI_Code_Review_Platform\test_codebases"
os.makedirs(test_dir, exist_ok=True)

# 1. Python Smells
python_code = """
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
"""

# 2. React TS Smells
react_code = """
import React, { useState, useEffect } from 'react';

export const UserDashboard: React.FC = () => {
    const [data, setData] = useState<any>(null);
    const [counter, setCounter] = useState(0);

    // Infinite loop smell: missing dependency array
    useEffect(() => {
        fetch('/api/user')
            .then(res => res.json())
            .then(resData => {
                setData(resData);
                setCounter(c => c + 1);
            });
    });

    return (
        <div>
            <h1>Dashboard (Counter: {counter})</h1>
            <button onClick={() => console.log('clicked')}>Click</button>
        </div>
    );
};
"""

# 3. C++ Smells
cpp_code = """
#include <iostream>
#include <cstring>

void process_input(const char* input) {
    char buffer[16];
    // Buffer overflow risk
    strcpy(buffer, input);
    std::cout << "Buffer: " << buffer << std::endl;
}

int main() {
    // Memory leak
    int* data = new int[100];
    process_input("This is a very long string that will overflow the buffer");
    return 0;
}
"""

def create_zip(name, filename, code):
    folder_path = os.path.join(test_dir, name)
    os.makedirs(folder_path, exist_ok=True)
    with open(os.path.join(folder_path, filename), "w", encoding="utf-8") as f:
        f.write(code.strip())
    
    zip_path = os.path.join(test_dir, f"{name}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(os.path.join(folder_path, filename), filename)
    print(f"Created zip: {zip_path}")

create_zip("python_smells", "main.py", python_code)
create_zip("react_smells", "App.tsx", react_code)
create_zip("cpp_smells", "main.cpp", cpp_code)
print("All zip files successfully created.")
