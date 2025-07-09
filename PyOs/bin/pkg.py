import os
import sys
import zipfile
import socket
import shutil, json
import tempfile
import time
ROOTFS = os.environ.get("ROOTFS")
REPO_DIR = os.path.join(ROOTFS,"repo")
INSTALL_DIR = os.path.join(ROOTFS,"usr")
PKGDB = os.path.join(ROOTFS,"var","pkgdb.txt")

def is_network_enabled():
    path = os.path.join(ROOTFS, "etc", "services", "ethernet.service")
    if not os.path.exists(path):
        return False
    with open(path) as f:
        svc = json.load(f)
    return svc.get("enabled", False)

def ensure_dirs():
    os.makedirs(REPO_DIR, exist_ok=True)
    os.makedirs(INSTALL_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(PKGDB), exist_ok=True)
    if not os.path.exists(PKGDB):
        with open(PKGDB, 'w') as f:
            pass

def install_pkg(name):
    ensure_dirs()
    zip_path = os.path.join(REPO_DIR, f"{name}.zip")

    if not os.path.exists(zip_path):
        print(f"[pkg] Local package not found: {name}")
        if not is_network_enabled():
            
            print("[pkg] Networking is disabled. Cannot fetch packages.")
            return

        print(f"[pkg] Attempting remote fetch from 192.168.0.150...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("192.168.0.150", 9000))
                s.sendall(name.encode() + b"\n")

                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmpf:
                    while True:
                        data = s.recv(4096)
                        if not data:
                            break
                        tmpf.write(data)
                    zip_path = tmpf.name
                    print(f"[pkg] Remote package {name} fetched successfully.")
        except Exception as e:
            print(f"[pkg] Failed to fetch remotely: {e}")
            return

    dest_dir = os.path.join(INSTALL_DIR, name)
    backup_dir = os.path.join("maninstall", name)

    # Backup if exists
    if os.path.exists(dest_dir):
        os.makedirs("maninstall", exist_ok=True)
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.move(dest_dir, backup_dir)
        print(f"[pkg] Existing package moved to maninstall/{name}")

    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)

    with open(PKGDB, 'a') as f:
        f.write(f"{name}\n")
    try_firstrun(name)
    print(f"[pkg] Installed {name}")
    time.sleep(1)  # Give it a moment to settle
def try_firstrun(name):
    exec_path = os.path.join(INSTALL_DIR, name, "exec.py")
    if not os.path.exists(exec_path):
        return

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(f"{name}_exec", exec_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "frun"):
            print(f"[pkg] Running firstrun for {name}...")
            module.frun()
        else:
            print(f"[pkg] No frun() in {name}/exec.py")
    except Exception as e:
        print(f"[pkg] Firstrun error: {e}")

def remove_pkg(name):
    dest_dir = os.path.join(INSTALL_DIR, name)
    if not os.path.exists(dest_dir):
        print(f"[pkg] Package not installed: {name}")
        return

    # Remove directory
    for root, dirs, files in os.walk(dest_dir, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
    os.rmdir(dest_dir)

    # Remove from pkgdb
    with open(PKGDB, 'r') as f:
        lines = f.readlines()
    with open(PKGDB, 'w') as f:
        for line in lines:
            if line.strip() != name:
                f.write(line)

    print(f"[pkg] Removed {name}")

def list_installed():
    with open(PKGDB, 'r') as f:
        pkgs = [line.strip() for line in f.readlines()]
    print("[pkg] Installed packages:")
    for p in pkgs:
        print(f"  {p}")

def search_repo():
    print("[pkg] Available packages:")
    for file in os.listdir(REPO_DIR):
        if file.endswith(".zip"):
            print(f"  {file[:-4]}")

def main():
    ensure_dirs()
    if len(sys.argv) < 2:
        print("[pkg] Usage: install/remove/list/search <name>")
        return
    cmd = sys.argv[1]
    if cmd == "install" and len(sys.argv) == 3:
        install_pkg(sys.argv[2])
        
    elif cmd == "remove" and len(sys.argv) == 3:
        remove_pkg(sys.argv[2])
    elif cmd == "list":
        list_installed()
    elif cmd == "search":
        search_repo()
    else:
        print("[pkg] Invalid command or arguments.")

if __name__ == "__main__":
    main()
