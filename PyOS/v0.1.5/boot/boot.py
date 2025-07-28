import zipfile
import os
import tempfile
import subprocess
import sys
import os

global preboot
global verbose

verbose = False
for i in range(1, len(sys.argv)):
    if sys.argv[i] == "-v":
        verbose = True
        continue
BOOT_DIR = os.path.abspath(os.path.dirname(__file__))
preboot = os.path.join(BOOT_DIR, 'preboot')
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

def printout(mess, verbose=False):
    if verbose:
        print(mess)
    else:
        pass




def remove_temp_dir(temp_dir):
    try:
        if os.path.exists(temp_dir):
            printout(f"[boot] Removing temporary kernel directory...", verbose)
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        printout(f"[boot] Failed to remove file {file_path}: {e}", verbose)
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    try:
                        os.rmdir(dir_path)
                    except Exception as e:
                        printout(f"[boot] Failed to remove directory {dir_path}: {e}", verbose)
    except Exception as e:
        printout(f"[boot] Failed to remove temporary directory {temp_dir}: {e}", verbose)
        # delete all files and folders inside the directory and try again
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    os.remove(file_path)
                except Exception as e:
                    printout(f"[boot] Failed to remove file {file_path}: {e}", verbose)
            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    os.rmdir(dir_path)
                except Exception as e:
                    printout(f"[boot] Failed to remove directory {dir_path}: {e}", verbose)
def is_drive_ready(drive_letter):
    try:
        return os.path.exists(drive_letter + "\\")
    except Exception:
        return False
def boot_kernel():
    if not os.path.exists(KERNEL_ZIP):
        printout("[boot] Kernel not found.", verbose)
        return

    temp_root = tempfile.mkdtemp(prefix="pyos_kernel_")
    printout(f"[boot] Extracting kernel to {temp_root}", verbose)
    os.environ["KERNEL_TEMP"] = temp_root
    
    with zipfile.ZipFile(KERNEL_ZIP, 'r') as zip_ref:
        zip_ref.extractall(temp_root)

    kernel_entry = os.path.join(temp_root, "init.py")
    try: 
        code = ["python", kernel_entry, '-fs', ROOT_FS, '-prb', preboot]
        for i in range(1, len(sys.argv)):
            code.append(sys.argv[i])

        code = subprocess.call(code)
    except KeyboardInterrupt:
        printout("[boot] Control-C", verbose)
        remove_temp_dir(temp_root)
        return
    if code == 0:
        printout("[boot] Kernel exited cleanly.", verbose)#
        remove_temp_dir(temp_root)
        exit(0)
    elif code == 4:
        printout("[boot] System Updated Rebooting...", verbose)
        remove_temp_dir(temp_root)
        boot_kernel()
    elif code == 5:
        printout("[boot] Rebooting...", verbose)
        remove_temp_dir(temp_root)
        boot_kernel()
    else:
        printout(f"[boot] Kernel exited with code {code}.", verbose)
        remove_temp_dir(temp_root)
def startdrive(temp_root):
    printout("[boot] Starting update process...", verbose)
    kernel_entry = os.path.join(temp_root, "update.py")
    code = subprocess.call(["python", kernel_entry, temp_root])
    if code == 0:
        printout("[boot] Update exited cleanly.", verbose)
        exit(0)
    else:
        printout(f"[boot] Update exited with code {code}.", verbose)
def scan_drives():
    printout("[verify] Scanning drives for PyOS installation media...\n", verbose)
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
            printout(f"[ok] {drive} contains a valid PyOS installer.", verbose)
            valid_drives.append(drive)

            # Optional: print metadata if JSON
            meta_path = os.path.join(drive, "metadata.json")
            try:
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
                printout("       > Metadata:"+ metadata, verbose)
            except Exception as e:
                printout("       > Failed to read metadata:"+ e, verbose)
            startdrive(drive)

        elif found_files:
            printout(f"[partial] {drive} has some files: {found_files}", verbose)
        else:
            printout(f"[skip] {drive} has no relevant files.", verbose)
    if not valid_drives:
        printout("[error] No valid PyOS installation media found.", verbose)
        boot_kernel()


if __name__ == "__main__":
    
    try:
        scan_drives()
    except Exception as e:
        printout(f"[boot] An error occurred: {e}", verbose)
        remove_temp_dir(os.environ.get("KERNEL_TEMP", ""))
        exit(1)
