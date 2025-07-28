import os
from datetime import datetime

LOG_FILE = os.path.join(os.environ.get("ROOTFS"), "var", "log", "boot.log")

def log_boot_event(event):
    print(event)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now()}] {event}\n")
