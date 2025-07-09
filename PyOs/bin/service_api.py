# /bin/service_api.py

import os
import json
import subprocess

ROOT = os.environ.get("ROOTFS")
print(f"[service] Using root directory: {ROOT}")
SERVICE_DIR = os.path.join(ROOT, "etc", "services")
print(f"[service] Service directory: {SERVICE_DIR}")
os.makedirs(SERVICE_DIR, exist_ok=True)

def register_service(name):
    ROOT = os.environ.get("ROOTFS")
    service_path = os.path.join(SERVICE_DIR, f"{name}.service")
    with open(service_path, "w") as f:
        config = {
        'exec': 'python ',
        "path": f'\\usr\\{name}\\daemon.py',
        "enabled": True
}
        json.dump(config, f)
    print(f"[service] Registered service '{name}'")

    if 1+1 == 2:  # Dummy condition to always run
        print(f"[service] Launching '{name}'...")
        subprocess.Popen(config["exec"] + ROOT+config["path"], shell=True)
