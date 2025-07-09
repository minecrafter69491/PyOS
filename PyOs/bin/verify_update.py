# etc/services/verify_update.service
import os
import string
import time
import sys

SCAN_INTERVAL = 5  # seconds between scans
REQUIRED_FILES = ["update.zip","update.py", "metadata.json"]
TMP_FILE = "tmp/update_drive.txt"

def is_valid_drive(drive):
    return all(os.path.exists(os.path.join(drive, f)) for f in REQUIRED_FILES)

def scan_once():
    for letter in string.ascii_uppercase:
        drive = f"{letter}:/"
        if os.path.exists(drive) and is_valid_drive(drive):
            # Save found drive path to a temp file for later use
            os.makedirs("tmp", exist_ok=True)
            with open(TMP_FILE, "w") as f:
                f.write(drive)
            return True
    return False

def main():
    print("[verify] Service started. Monitoring for install media...")
    while True:
        if scan_once():
            print("[verify] Valid update media found.\n[verify]please reboot to install.")
            exit()  # Signal service manager
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
