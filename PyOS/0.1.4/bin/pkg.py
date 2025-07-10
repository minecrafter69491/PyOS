import os
import sys
import zipfile
import socket
import shutil, json
import tempfile
import time
import requests
from colorama import Fore, Style
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
    dest_dir = os.path.join(ROOTFS, "usr", name)
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
        print(f"[pkg] Existing {name} package removed.")

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

def install_system(name):
    ensure_dirs()
    zip_path = os.path.join(REPO_DIR, f"{name}.zip")
    if not os.path.exists(zip_path):
        print(f"[pkg] Local package not found: {name}")
        return
    dest_dir = os.environ.get("ROOTFS")  # Default to root if not set
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)

    print(f"[pkg] Installed system version {name}")
    sys.exit(4)  


def update(name):
    #ensure_dirs()
    zip_path = os.path.join(REPO_DIR, f"{name}.zip")
    if not is_network_enabled():
            print("[pkg] Networking is disabled. Cannot fetch packages.")
            return
    if name == "system":
            import requests
            print(f'[pkg] Fetching system update from GitHub...')
            import shell
            osver = shell.info['PYOS_VERSION']
            update_url = "https://raw.githubusercontent.com/minecrafter69491/PyOS/refs/heads/main/Packages/system.txt"
            response = requests.get(update_url)
            if response.status_code == 200:
                osverd = response.content.strip()
                if osverd != osver:
                    print(f"[pkg] System update available: {Fore.RED +osver+    Style.RESET_ALL} -> {Fore.GREEN + osverd.decode("utf-8") + Style.RESET_ALL}")
                    update_url = f"https://github.com/minecrafter69491/PyOS/releases/download/v{osverd.decode("utf-8")}/V{osverd.decode("utf-8")}.zip"
                    print(f"[pkg] Downloading update from {update_url}")
                    response = requests.get(update_url)
                    if response.status_code == 200:
                        with open(zip_path, 'wb') as f:
                            f.write(response.content)
                        print(f"[pkg] Remote package {name} fetched successfully.")
                        install_system(name)
                        return
                    else:
                        print(f"[pkg] Failed to fetch {name}: {response.status_code}")
                        return

                
            else:
                print(f"[pkg] Failed to fetch {name}: {response.status_code}")
                return
    print(f"[pkg] Attempting remote fetch from GitHub...")
    try:
            import requests
            update_url = f"https://raw.githubusercontent.com/minecrafter69491/PyOS/refs/heads/main/Packages/{name}.zip"
            response = requests.get(update_url)
            if response.status_code == 200:
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                print(f"[pkg] Remote package {name} fetched successfully.")
                install_pkg(name)
            else:
                print(f"[pkg] Failed to fetch {name}: {response.status_code}")
                return
    except Exception as e:
            print(f"[pkg] Failed to fetch remotely: {e}")
            return
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
        print("[pkg] Usage: install/remove/list/update/search <name>")
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
    elif cmd == "update" and len(sys.argv) == 3:
        print(f"[pkg] Updating {sys.argv[2]}...")
        update(sys.argv[2])
    else:
        print("[pkg] Invalid command or arguments.")

if __name__ == "__main__":
    main()
