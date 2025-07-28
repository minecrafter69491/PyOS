import sys
import os
import subprocess


def frun():
    ...

def popup(file, args):
    # Path to the other Python script

    # Launch it in a new console window on Windows
    if sys.platform == "win32":
        subprocess.Popen(
            ["python", file] + args,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # On Linux/macOS, just run it normally (will still run in background)
        subprocess.Popen(["python3", file] + args)


def main(args):
    if args[0] == "shell":
        print("[exec] Launching shell...")
        login = os.path.join(os.environ.get('KERNEL_TEMP'), "login.py")
        popup(login, [os.environ.get('ROOTFS')])

    if args[0] == "close":
        print("[exec] Closing Pit...")
        pit_path = os.path.join(os.environ.get('ROOTFS'), 'dev', f'pit{args[1]}')
        if not os.path.exists(pit_path):
            print(f"[exec] Pit {args[1]} does not exist.")
        with open(pit_path, 'r') as f:
            pid = f.read().strip()
        try:
            pid = int(pid)
        except ValueError:
            print(f"[exec] Invalid PID in {pit_path}: {pid}")
        try:
            os.kill(pid, 9)  # Force kill the process
            print(f"[exec] Process {pid} killed.")
        except OSError as e:
            print(f"[exec] Error killing process {pid}: {e}")
        if os.path.exists(pit_path):
            os.remove(pit_path)
        print("[exec] Pit closed.")
            
