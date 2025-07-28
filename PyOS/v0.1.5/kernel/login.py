import os
import sys
import getpass
import subprocess

def load_users(passwd_file):
    users = {}
    if os.path.exists(passwd_file):
        with open(passwd_file, "r") as f:
            for line in f:
                if ':' in line:
                    user, pw = line.strip().split(':', 1)
                    users[user] = pw
    return users

def login(users):
    print("[login] Welcome to PyOS")
    for _ in range(3):
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        if username in users and users[username] == password:
            print(f"[login] Login successful. Welcome, {username}!")
            return username
        print("[login] Invalid credentials.")
    print("[login] Too many failed attempts.")
    return None

def start_shell(root_fs, username):
    shell = os.path.join(root_fs, "bin", "shell.py")
    return subprocess.call(["python", shell, username])  # Returns shell's exit code

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[login] Error: No root path provided.")
        sys.exit(1)

    root_fs = sys.argv[1]
    passwd = os.path.join(root_fs, "etc", "passwd")
    users = load_users(passwd)

    while True:
        user = login(users)
        if user:
            try:
                result = start_shell(root_fs, user)
                if result == 1:
                    print("[login] Shutdown requested.")
                    break
                elif result == 4:
                    print("[login] System package installed. Rebooting system...")
                    sys.exit(4)
                if result == 5:
                    print("[login] Rebooting system...")
                    sys.exit(5)
            except KeyboardInterrupt:
                print("[login] Control-C detected. Exiting shell.")
                result = 0
            
