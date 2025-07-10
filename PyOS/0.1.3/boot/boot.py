import zipfile
import os
import tempfile
import subprocess
import sys
import os

BOOT_DIR = os.path.abspath(os.path.dirname(__file__))
KERNEL_ZIP = os.path.join(BOOT_DIR, "..", "kernel.zip")
ROOT_FS = os.path.abspath(os.path.join(BOOT_DIR, ".."))
os.environ["ROOTFS"] = ROOT_FS

custom_dir = os.path.abspath(os.path.join(BOOT_DIR, "bin"))  # or any path you want
if custom_dir not in sys.path:
    sys.path.insert(0, custom_dir)

import os
import string
import json

REQUIRED_FILES = [
    "update.zip",
    "update.py",
    "metadata.json",  # You can also check for .txt if needed
]

def is_drive_ready(drive_letter):
    try:
        return os.path.exists(drive_letter + "\\")
    except Exception:
        return False
def boot_kernel():
    if not os.path.exists(KERNEL_ZIP):
        print("[boot] Kernel not found.")
        return

    temp_root = tempfile.mkdtemp(prefix="pyos_kernel_")
    print(f"[boot] Extracting kernel to {temp_root}")
    os.environ["KERNEL_TEMP"] = temp_root
    
    with zipfile.ZipFile(KERNEL_ZIP, 'r') as zip_ref:
        zip_ref.extractall(temp_root)

    kernel_entry = os.path.join(temp_root, "init.py")
    code = subprocess.call(["python", kernel_entry, ROOT_FS])
    if code == 0:
        print("[boot] Kernel exited cleanly.")
        exit(0)
    else:
        print(f"[boot] Kernel exited with code {code}.")
def startdrive(temp_root):
    print("[boot] Starting update process...")
    kernel_entry = os.path.join(temp_root, "update.py")
    code = subprocess.call(["python", kernel_entry, temp_root])
    if code == 0:
        print("[boot] Update exited cleanly.")
        exit(0)
    else:
        print(f"[boot] Update exited with code {code}.")
def scan_drives():
    print("[verify] Scanning drives for PyOS installation media...\n")
    valid_drives = []

    for letter in string.ascii_uppercase:
        drive = f"{letter}:/"
        if not is_drive_ready(drive):
            continue

        found_files = []
        for fname in REQUIRED_FILES:
            if os.path.exists(os.path.join(drive, fname)):
                found_files.append(fname)

        if len(found_files) == len(REQUIRED_FILES):
            print(f"[ok] {drive} contains a valid PyOS installer.")
            valid_drives.append(drive)

            # Optional: print metadata if JSON
            meta_path = os.path.join(drive, "metadata.json")
            try:
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
                print("       > Metadata:", metadata)
            except Exception as e:
                print("       > Failed to read metadata:", e)
            startdrive(drive)

        elif found_files:
            print(f"[partial] {drive} has some files: {found_files}")
        else:
            print(f"[skip] {drive} has no relevant files.")
    if not valid_drives:
        print("[error] No valid PyOS installation media found.")
        boot_kernel()


if __name__ == "__main__":
    try:
        scan_drives()
    except Exception as e:
        print(f"[boot] An error occurred: {e}")
        exit(1)
