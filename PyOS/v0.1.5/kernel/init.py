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
from LoadPreboot import boot_preboot_env

global verbose, debug, rootfs, prb

verbose = os.environ.get("VERBOSE", "0")
if verbose == "1":
    verbose = True
else:
    verbose = False
debug = False
rootfs = False
prb = False
BOOT_TIME = time.time()
SERVICE_DIR = os.path.join(os.environ.get('ROOTFS'), "etc", "services")
AUTO_SERVICES = {}

def printout(mess, verbose=False):
    if verbose:
        print(mess)
    else:
        pass

def cmd_kill(args, verbose=False):
    try:
        pid = int(args)
        p = psutil.Process(pid)
        p.terminate()
        printout(f"Process {pid} terminated.", verbose)
    except Exception as e:
        printout(f"Error: {e}", verbose)

import os
import json

def on_shutdown(verbose=False):
    printout("[init] Shutting down services...", verbose)

    # Load JSON string from environment
    retrieved = json.loads(os.environ['service'])

    # Get service names and PIDs
    services = retrieved['service']
    pids = retrieved['wpid']

    for name, proc in zip(services, pids):
        try:
            printout(f"[init] Stopping service: {name} (PID: {proc})", verbose)
            cmd_kill(proc, verbose)  # Assuming cmd_kill is defined elsewhere
            printout(f"[init] Service {name} stopped successfully.", verbose)
        except Exception as e:
            printout(f"[init] Error stopping service {name}: {e}", verbose)

    printout("[init] All services stopped.", verbose)
    printout("[init] System shutdown complete.", verbose)
    printout("SYSTEM IS GOING DOWN NOW!!!", verbose)

def get_runtime():
    seconds = int(time.time() - BOOT_TIME)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours}h {mins}m {secs}s"

def autostart_services(verbose=False):
    printout("[init] Autostarting enabled services...", verbose)
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
            printout(f"[init] Skipping disabled service: {fname}", verbose)
            continue
        name = fname.replace(".service", "")
        if svc.get("enabled", True):
            pid_num += 1
            printout(f"[init] Starting service: {name}", verbose)
            service.append(name)
            pid.append(pid_num)
            spath.append(svc['path'])
            proc = subprocess.Popen(svc["exec"]+os.environ.get('ROOTFS')+svc['path'], shell=True)
            printout(f"[init] Service {name} started with PID {proc.pid}", verbose)
            wpid.append(proc.pid)
            AUTO_SERVICES[name] = proc
    data = {'service': service, 'pid': pid, 'path': path, 'mpid': pid_num, 'wpid': wpid}
    data_str = json.dumps(data)
    os.environ['service'] = data_str
    time.sleep(waitamount)

class VirtualFileSystem:
    def __init__(self, root=None, verbose=False):
        self.verbose = verbose
        self.root = root or tempfile.mkdtemp(prefix="pyos_root_")
        self.mounts = []
        printout(f"[init] Virtual root created at: {self.root}", verbose)

    def make_dir(self, path):
        full_path = os.path.join(self.root, path.strip("/").replace("/", os.sep))
        os.makedirs(full_path, exist_ok=True)
        printout(f"[init] Created directory: /{path}", self.verbose)
        return full_path

    def create_standard_layout(self):
        for path in ["/bin", "/etc", "/home", "/mnt", "/usr", "/var", "/tmp"]:
            self.make_dir(path)

    def detect_and_mount_drives(self):
        printout("[init] Detecting drives...", self.verbose)
        for letter in string.ascii_uppercase:
            if letter == "C":
                continue
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                mount_point = f"/mnt/{letter.lower()}"
                target = os.path.join(self.root, mount_point.strip("/").replace("/", os.sep))
                try:
                    os.symlink(drive, target, target_is_directory=True)
                    printout(f"[init] Mounted {drive} -> {mount_point} (symlink)", self.verbose)
                except (OSError, NotImplementedError):
                    # Fallback: copy drive letter as a real folder
                    os.makedirs(target, exist_ok=True)
                    printout(f"[init] Mounted {drive} -> {mount_point} (real dir fallback)", self.verbose)
                self.mounts.append((drive, mount_point))

    def show_mounts(self):
        printout("[init] Mounted drives:", self.verbose)
        for src, dest in self.mounts:
            printout(f"  {src} -> {dest}", self.verbose)
def ensure_root_dirs(root):
    for d in ["etc", "bin", "home", "var"]:
        os.makedirs(os.path.join(root, d), exist_ok=True)

def launch_login(root_fs, verbose=False):
    login_path = os.path.join(os.path.dirname(__file__), "login.py")
    proc = subprocess.call(["python", login_path, root_fs])
    if proc == 0:
        printout("[init] Shutting Down...", verbose)
        on_shutdown(verbose)
        sys.exit(0)
    if proc == 4:
        printout("[init] System package installed. Rebooting system...", verbose)
        on_shutdown(verbose)
        sys.exit(4)
    if proc == 5:
        printout("[init] Rebooting system...", verbose)
        on_shutdown(verbose)
        sys.exit(5)

def main():
    verbose = False
    debug = False
    root_fs = False
    prb = False
    if len(sys.argv) < 5:
        printout("Invalid  Usage.", verbose)
        sys.exit(1)#
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == "-fs":
            root_fs = sys.argv[i + 1]
            printout(f"Root filesystem set to: {root_fs}", verbose)
            continue
        if sys.argv[i] == "-prb":
            prb = sys.argv[i + 1]
            printout(f"Preboot Enviroment set to: {prb}", verbose)
            continue
        if sys.argv[i] == "-v":
            verbose = True
            os.environ["VERBOSE"] = "1"
            printout("Verbose mode enabled.", verbose)
            continue
        if sys.argv[i] == "debug=0x100":
            verbose = True
            debug = True
            printout("Debug mode enabled with level 0x100.", verbose)
            continue
    if not prb:
        printout("Preboot environment path is required.", verbose)
        sys.exit(1)
    if not root_fs:
        printout("Root filesystem path is required.", verbose)
        sys.exit(1)
    if not os.path.exists(prb):
        printout(f"Preboot environment path does not exist: {prb}", verbose)
        sys.exit(1)
    if not os.path.exists(root_fs):
        printout(f"Root filesystem path does not exist: {root_fs}", verbose)
        sys.exit(1)
    printout("Starting kernel initialization...", verbose)
    printout('Booting kernel with the following parameters: ', verbose)
    printout(sys.argv[1:], verbose)
    printout('Booting Preboot Environment...', verbose)
    boot_preboot_env(prb, verbose)
    printout(f"[init] Booting with root filesystem: {root_fs}", verbose)
    ensure_root_dirs(root_fs)
    
    vfs = VirtualFileSystem(root=root_fs)
    vfs.create_standard_layout()
    vfs.detect_and_mount_drives()
    vfs.show_mounts()

    # Optional: start other services or shells here
    autostart_services(verbose)
    printout(f"[init] Init complete. OS root is: {vfs.root}", verbose)
    try:
        launch_login(root_fs, verbose)
    except KeyboardInterrupt:
        pass
    
if __name__ == "__main__":
    main()
