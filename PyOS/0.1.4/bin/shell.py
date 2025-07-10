import sys
import os
from colorama import Fore, Style
import subprocess
import json
import os
import subprocess
import signal
import shutil
import platform
import time

custom_dir = os.path.abspath(os.environ.get('KERNEL_TEMP') )

if custom_dir not in sys.path:
        sys.path.insert(0, custom_dir)

root_fs = os.environ.get("ROOTFS")
SERVICE_DIR = os.path.join(root_fs, "etc", "services")
SERVICE_PROCS = {}  # service name -> subprocess

import psutil

def cmd_ps_windows(args):
    print(f"{'PID':>6} {'Name':<25} {'Status':<10}")
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            status = proc.info['status']
            print(f"{pid:>6} {name:<25} {status:<10}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
def cmd_kill(args):
    if len(args) < 1:
        print("Usage: kill PID")
        return
    try:
        pid = int(args[0])
        p = psutil.Process(pid)
        p.terminate()
        print(f"Process {pid} terminated.")
    except Exception as e:
        print(f"Error: {e}")
def cmd_df(args):
    total, used, free = shutil.disk_usage("/")
    print(f"Filesystem      Size    Used    Free")
    print(f"/           {total // (2**30)}G   {used // (2**30)}G   {free // (2**30)}G")
import os

def cmd_du(args):
    path = args[0] if len(args) > 0 else "."
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    print(f"{path}: {total_size // 1024} KB")
def cmd_free(args):
    vm = psutil.virtual_memory()
    print(f"Total: {vm.total // (1024**2)} MB")
    print(f"Used:  {vm.used // (1024**2)} MB")
    print(f"Free:  {vm.available // (1024**2)} MB")

def load_users(USER_FILE):
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, "r") as f:
        return [line.strip().split(":") for line in f if line.strip()]

def save_users(users, USER_FILE):
    with open(USER_FILE, "w") as f:
        for user in users:
            f.write(":".join(user) + "\n")

def create_user(username, password, is_admin=False):
    root_fs = os.environ.get("ROOTFS")
    HOME_DIR = os.path.join(root_fs, "home")
    USER_FILE = os.path.join(root_fs, "etc")
    USER_FILE = USER_FILE + "\\passwd"
    if not username or ":" in username:
        raise ValueError("Invalid username")

    users = load_users(USER_FILE)
    if any(u[0] == username for u in users):
        raise ValueError(f"User '{username}' already exists")

    hashed_pw = password
    users.append([username, hashed_pw])
    save_users(users, USER_FILE)

    # Create home directory
    user_home = os.path.join(HOME_DIR, username)
    os.makedirs(user_home, exist_ok=True)

    print(f"[user] Created user '{username}'")

def delete_user(username):
    root_fs = os.environ.get("ROOTFS")
    HOME_DIR = os.path.join(root_fs, "home")
    USER_FILE = os.path.join(root_fs, "etc", "passwd")
    users = load_users(USER_FILE)
    users = [u for u in users if u[0] != username]
    save_users(users, USER_FILE)

    # Delete home directory
    user_home = os.path.join(HOME_DIR, username)
    if os.path.exists(user_home):
        shutil.rmtree(user_home)

    print(f"[user] Deleted user '{username}' and removed home.")

def get_kernel_version():
    # Find the kernel path from temp environment or default location
    temp_root = os.getenv("KERNEL_TEMP")
    if not temp_root:
        return "Unknown"

    version_file = os.path.join(temp_root, "kernel_version")
    if os.path.exists(version_file):
        with open(version_file) as f:
            return f.read().strip()
    return "Unknown"
def exit():
    print("[shell] Exiting shell...")
    # Signal to the service manager that the shell is exiting
    sys.exit(1)
def run_touch(args):
    if not args:
        print("Usage: touch <file>")
        return
    path = os.path.join(os.getcwd(), args[0])
    try:
        open(path, "a").close()
    except Exception as e:
        print("touch error:", e)
def run_rm(args):
    if not args:
        print("Usage: rm <file_or_dir>")
        return
    path = os.path.join(os.getcwd(), args[0])
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except Exception as e:
        print("rm error:", e)
def run_mkdir(args):
    if not args:
        print("Usage: mkdir <dir>")
        return
    try:
        os.makedirs(os.path.join(os.getcwd(), args[0]))
    except Exception as e:
        print("mkdir error:", e)
info = {
        "PYOS_NAME": "PyOs Developer Preview",
        "PYOS_VERSION": "0.1.3",
        "KERNEL_VERSION": get_kernel_version(),
    }
def run_info():
    from init import get_runtime  # or any path you want
    release_path = os.path.join(root_fs, "etc", "pyos-release")
    

    if os.path.exists(release_path):
        with open(release_path) as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    info[k] = v

    print(f"{info['PYOS_NAME']} {info['PYOS_VERSION']}")
    print(f"Kernel version: {get_kernel_version()}")
    print(f"Python version: {platform.python_version()}")
    print(f"Uptime: {get_runtime()}")
def run_service_command(args):
    if not args:
        print("[service] Usage: service <list|start|stop|enable|disable> [name]")
        return

    cmd = args[0]

    if cmd == "list":
        services = os.listdir(SERVICE_DIR)
        for svc_file in services:
            with open(os.path.join(SERVICE_DIR, svc_file)) as f:
                svc = json.load(f)
                name = svc_file.replace(".service", "")
                status = "running" if name in SERVICE_PROCS else "stopped"
                enabled = "enabled" if svc.get("enabled") else "disabled"
                print(f"{name}: {status}, {enabled}")

    elif cmd in ("start", "stop", "enable", "disable"):
        if len(args) < 2:
            print(f"[service] Missing service name for '{cmd}'")
            return

        name = args[1]
        path = os.path.join(SERVICE_DIR, f"{name}.service")

        if not os.path.exists(path):
            print(f"[service] No such service: {name}")
            return

        with open(path, "r") as f:
            svc = json.load(f)

        if cmd == "start":
            if name in SERVICE_PROCS:
                print(f"[service] {name} already running.")
            else:
                proc = subprocess.Popen(svc["exec"]+root_fs+svc['path'], shell=True)
                
                if proc.returncode == 0:
                    print(f"[service] {name} exited with code 0.")
                    # Signal update to shell or init
                SERVICE_PROCS[name] = proc
                print(f"[service] Started {name}.")
                time.sleep(1)
                if proc.returncode == 400:
                    print('i am him')
                    sys.exit(1)  # Give it a moment to start
                mpid = os.environ.get("service")['mpid']
                service_list = os.environ.get("service")['service']
                pid_list = os.environ.get("service")['pid']
                path_list = os.environ.get("service")['path']
                # add the service to the service list
                service_list.append(name)
                pid_list.append(mpid + 1)
                path_list.append(f'\\usr\\{name}\\daemon.py')
                os.environ['service'] = {
                    'service': service_list,
                    'pid': pid_list,
                    'path': path_list,
                    'mpid': mpid + 1
                }
            try:
                service_path = os.path.join(SERVICE_DIR, f"{name}.service")
                with open(service_path, "r") as f:
                        service_data = json.load(f)
                        service_data["enabled"] = True
                        with open(service_path, "w") as f:
                            json.dump(service_data, f, indent=4)
                        print(f"[service] {name} Enabled in service file.")
            except Exception as e:
                    print(f"[service] Failed to update service file: {e}")
        elif cmd == "stop":
            proc = SERVICE_PROCS.get(name)
            if proc:
                proc.terminate()
                SERVICE_PROCS.pop(name)
                print(f"[service] Stopped {name}.")
            else:
                print(f"[service] {name} is not running.")
            
            try:
                service_path = os.path.join(SERVICE_DIR, f"{name}.service")
                with open(service_path, "r") as f:
                        service_data = json.load(f)
                        service_data["enabled"] = False
                        with open(service_path, "w") as f:
                            json.dump(service_data, f, indent=4)
                        print(f"[service] {name} disabled in service file.")
            except Exception as e:
                    print(f"[service] Failed to update service file: {e}")

        elif cmd == "enable":
            svc["enabled"] = True
            with open(path, "w") as f:
                json.dump(svc, f)
            print(f"[service] Enabled {name}.")
            mpid = os.environ.get("service")['mpid']
            service_list = os.environ.get("service")['service']
            pid_list = os.environ.get("service")['pid']
            path_list = os.environ.get("service")['path']
            # add the service to the service list
            service_list.append(name)
            pid_list.append(mpid + 1)
            path_list.append(f'\\usr\\{name}\\daemon.py')
            os.environ['service'] = {
                    'service': service_list,
                    'pid': pid_list,
                    'path': path_list,
                    'mpid': mpid + 1
            }

        elif cmd == "disable":
            svc["enabled"] = False
            with open(path, "w") as f:
                json.dump(svc, f)
            print(f"[service] Disabled {name}.")


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_virtual_path(cwd, root_fs):
    # Remove the root prefix and replace backslashes
    path = os.path.relpath(cwd, root_fs).replace('\\', '/')
    return '/' if path == '.' else f'/{path}'

def run_shell(user, user_home):
    root_fs = os.environ.get('ROOTFS')  # Assume current working dir is /
    cwd = os.getcwd()
    print(f"[shell] Logged in as {user}. Type 'help' for commands.")
    run_info()

    try:
        while True:
            try:
                if os.getcwd() == user_home:
                    virtual_path = "~"
                else:
                    virtual_path = get_virtual_path(cwd, root_fs)
                cmd_input = input(f"{Fore.GREEN}{user}@{'pyos'}:{Fore.BLUE}{virtual_path} {Style.RESET_ALL}$ ").strip()
                if not cmd_input:
                    continue

                parts = cmd_input.split()
                cmd = parts[0]
                args = parts[1:]

                if cmd == "exit":
                    print("[shell] Logging out...")
                    return 0

                elif cmd == "edit":
                    if len(args) != 1:
                        print("[shell] Usage: edit <filename>")
                    else:
                        editor = os.path.join(root_fs, "bin", "editor.py")
                        subprocess.call(["python", editor, os.path.join(cwd, args[0])])

                elif cmd == "pkg":
                    proc = subprocess.call(["python", os.path.join(root_fs, "bin", "pkg.py")] + args)
                    if proc == 4:
                        print("[shell] System package installed. Rebooting system...")
                        sys.exit(4)
                elif cmd == "reboot" and args == ["-s"]:
                    print("[shell] Shutting down...")
                    return 1
                elif cmd == "reboot":
                    print("[shell] Rebooting...")
                    sys.exit(5)

                elif cmd == "users" and args[0] == "add":
                    create_user(args[1], args[2])

                elif cmd == "users" and args[0] == "del":
                    delete_user(args[1])

                elif cmd == "users":
                    print("[shell] Usage: users add <username> <password> | del <username>")

                elif cmd == "whoami":
                    print(user)

                elif cmd == "touch":
                    run_touch(args)
                elif cmd == "df":
                    cmd_df(args)   
                elif cmd == "du":
                    cmd_du(args)
                elif cmd == "free":
                    cmd_free(args)
                elif cmd == "kill":
                    cmd_kill(args)
                elif cmd == "ps": 
                    if args[0] and args[0] == "windows":
                        cmd_ps_windows(args)
                elif cmd == "mv":
                    if len(args) != 2:
                        print("Usage: mv <source> <destination>")
                    else:
                        src = os.path.join(cwd, args[0])
                        dst = os.path.join(cwd, args[1])
                        try:
                            shutil.move(src, dst)
                            print(f"Moved {args[0]} to {args[1]}")
                        except Exception as e:
                            print("Error:", e)

                elif cmd == "cp":
                    if len(args) != 2:
                        print("Usage: cp <source> <destination>")
                    else:
                        src = os.path.join(cwd, args[0])
                        dst = os.path.join(cwd, args[1])
                        try:
                            if os.path.isdir(src):
                                shutil.copytree(src, dst)
                            else:
                                shutil.copy2(src, dst)
                            print(f"Copied {args[0]} to {args[1]}")
                        except Exception as e:
                            print("Error:", e)

                elif cmd == "rename":
                    if len(args) != 2:
                        print("Usage: rename <old_name> <new_name>")
                    else:
                        src = os.path.join(cwd, args[0])
                        dst = os.path.join(cwd, args[1])
                        try:
                            os.rename(src, dst)
                            print(f"Renamed {args[0]} to {args[1]}")
                        except Exception as e:
                            print("Error:", e)

                elif cmd == "rm":
                    run_rm(args)

                elif cmd == "mkdir":
                    run_mkdir(args)

                elif cmd == "service":
                    run_service_command(args)

                elif cmd == "info":
                    run_info()

                elif cmd == "py":
                    print("Entering Python console. Type exit() or Ctrl+D to return.")
                    import code
                    code.interact(local=globals())

                elif cmd == "help":
                    print("""Available commands:
  whoami          Show current user
  pwd             Show current directory
  ls              List directory contents
  cd <dir>        Change directory
  cat <file>      Show file contents
  echo <text>     Print text
  clear           Clear the screen
  exit            Log out
  reboot -s       Shut down PyOS""")

                elif cmd == "pwd":
                    print(virtual_path)

                elif cmd == "ls":
                    try:
                        files = os.listdir(cwd)
                        for f in files:
                            print(f)
                    except Exception as e:
                        print(f"[shell] Error: {e}")
                elif cmd == "cd" and args == ['/']:
                    os.chdir(root_fs)
                    cwd = root_fs
                elif cmd == "cd":
                    if len(args) != 1:
                        print("[shell] Usage: cd <directory>")
                    else:
                        new_dir = os.path.abspath(os.path.join(cwd, args[0]))
                        if os.path.isdir(new_dir) and new_dir.startswith(root_fs):
                            cwd = new_dir
                            os.chdir(cwd)
                        else:
                            print("[shell] No such directory.")
                

                elif cmd == "cat":
                    if len(args) != 1:
                        print("[shell] Usage: cat <filename>")
                    else:
                        try:
                            with open(os.path.join(cwd, args[0]), 'r') as f:
                                print(f.read())
                        except Exception as e:
                            print(f"[shell] Error reading file: {e}")

                elif cmd == "echo":
                    print(" ".join(args))

                elif cmd == "clear":
                    clear_screen()

                else:
                    app_path = os.path.join(root_fs, "usr", cmd, "exec.py")
                    if os.path.exists(app_path):
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(f"{cmd}_exec", app_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        if hasattr(module, "main"):
                            if args == []:
                                args = ''
                            module.main(args)
                        else:
                            print(f"[shell] Error: {cmd} package has no main()")
                    else:
                        print(f"[shell] Unknown command: {cmd}")

            except Exception as e:
                print(f"[shell] Error When Executing {cmd}: {e}")

    except KeyboardInterrupt:
        print("\n[shell] ^C")
        pass


if __name__ == "__main__":
    try:
        username = sys.argv[1] if len(sys.argv) > 1 else "unknown"
        user_home = os.path.join(os.environ.get('ROOTFS'), "home", username)
        os.chdir(user_home)
        code = run_shell(username, user_home)
        sys.exit(code)
    except KeyboardInterrupt:
        print("\n[shell] ^C")
