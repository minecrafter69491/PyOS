import os
import sys
import subprocess
import string
import tempfile
import shutil
import ctypes
import json
import subprocess
import os
import time
import psutil
BOOT_TIME = time.time()


SERVICE_DIR = os.path.join(os.environ.get('ROOTFS'), "etc", "services")
AUTO_SERVICES = {}
def cmd_kill(args):
    try:
        pid = int(args)
        p = psutil.Process(pid)
        p.terminate()
        print(f"Process {pid} terminated.")
    except Exception as e:
        print(f"Error: {e}")

import os
import json

def on_shutdown():
    print("[init] Shutting down services...")

    # Load JSON string from environment
    retrieved = json.loads(os.environ['service'])

    # Get service names and PIDs
    services = retrieved['service']
    pids = retrieved['wpid']

    for name, proc in zip(services, pids):
        try:
            print(f"[init] Stopping service: {name} (PID: {proc})")
            cmd_kill(proc)  # Assuming cmd_kill is defined elsewhere
            print(f"[init] Service {name} stopped successfully.")
        except Exception as e:
            print(f"[init] Error stopping service {name}: {e}")

    print("[init] All services stopped.")
    print("[init] System shutdown complete.")
    print("SYSTEM IS GOING DOWN NOW!!!")

def get_runtime():
    seconds = int(time.time() - BOOT_TIME)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours}h {mins}m {secs}s"

def autostart_services():
    print("[init] Autostarting enabled services...")
    waitamount = 1
    service = []
    pid = []
    spath = []
    wpid = []
    pid_num = 0
    for fname in os.listdir(SERVICE_DIR):
        if not fname.endswith(".service"):
            continue
        waitamount=waitamount+0.1
        path = os.path.join(SERVICE_DIR, fname)
        with open(path, "r") as f:
            svc = json.load(f)
        if svc.get("disabled", False):
            print(f"[init] Skipping disabled service: {fname}")
            continue
        name = fname.replace(".service", "")
        if svc.get("enabled", True):
            pid_num += 1
            print(f"[init] Starting service: {name}")
            service.append(name)
            pid.append(pid_num)
            spath.append(svc['path'])
            proc = subprocess.Popen(svc["exec"]+os.environ.get('ROOTFS')+svc['path'], shell=True)
            print(f"[init] Service {name} started with PID {proc.pid}")
            wpid.append(proc.pid)
            AUTO_SERVICES[name] = proc
    data = {'service': service, 'pid': pid, 'path': path, 'mpid': pid_num, 'wpid': wpid}
    data_str = json.dumps(data)
    os.environ['service'] = data_str
    time.sleep(waitamount)

class VirtualFileSystem:
    def __init__(self, root=None):
        self.root = root or tempfile.mkdtemp(prefix="pyos_root_")
        self.mounts = []
        print(f"[init] Virtual root created at: {self.root}")

    def make_dir(self, path):
        full_path = os.path.join(self.root, path.strip("/").replace("/", os.sep))
        os.makedirs(full_path, exist_ok=True)
        print(f"[init] Created directory: /{path}")
        return full_path

    def create_standard_layout(self):
        for path in ["/bin", "/etc", "/home", "/mnt", "/usr", "/var", "/tmp"]:
            self.make_dir(path)

    def detect_and_mount_drives(self):
        print("[init] Detecting drives...")
        for letter in string.ascii_uppercase:
            if letter == "C":
                continue
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                mount_point = f"/mnt/{letter.lower()}"
                target = os.path.join(self.root, mount_point.strip("/").replace("/", os.sep))
                try:
                    os.symlink(drive, target, target_is_directory=True)
                    print(f"[init] Mounted {drive} -> {mount_point} (symlink)")
                except (OSError, NotImplementedError):
                    # Fallback: copy drive letter as a real folder
                    os.makedirs(target, exist_ok=True)
                    print(f"[init] Mounted {drive} -> {mount_point} (real dir fallback)")
                self.mounts.append((drive, mount_point))

    def show_mounts(self):
        print("[init] Mounted drives:")
        for src, dest in self.mounts:
            print(f"  {src} -> {dest}")
def ensure_root_dirs(root):
    for d in ["etc", "bin", "home", "var"]:
        os.makedirs(os.path.join(root, d), exist_ok=True)

def launch_login(root_fs):
    login_path = os.path.join(os.path.dirname(__file__), "login.py")
    proc = subprocess.call(["python", login_path, root_fs])
    if proc == 0:
        print("[init] Shutting Down...")
        on_shutdown()
        sys.exit(0)
    if proc == 4:
        print("[init] System package installed. Rebooting system...")
        on_shutdown()
        sys.exit(4)
    if proc == 5:
        print("[init] Rebooting system...")
        on_shutdown()
        sys.exit(5)

def main():
    if len(sys.argv) < 2:
        print("[init] Error: Root filesystem path not provided.")
        return

    root_fs = os.path.abspath(sys.argv[1])
    print(f"[init] Booting with root filesystem: {root_fs}")
    ensure_root_dirs(root_fs)
    
    vfs = VirtualFileSystem(root=root_fs)
    vfs.create_standard_layout()
    vfs.detect_and_mount_drives()
    vfs.show_mounts()

    # Optional: start other services or shells here
    autostart_services()
    print(f"[init] Init complete. OS root is: {vfs.root}")
    try:
        launch_login(root_fs)
    except KeyboardInterrupt:
        pass
    
if __name__ == "__main__":
    main()
