import os
import subprocess
import json



def printout(mess, verbose=False):
    if verbose:
        print(mess)
    else:
        pass
    

def boot_preboot_env(path, verbose=False):
    KEXTS_PATH = os.path.join(path, 'kexts')
    DRIVERS_PATH = os.path.join(path, 'drivers')
    if not os.path.exists(KEXTS_PATH):
        printout("[kext] No kexts path found.")
        return

    for root, dirs, files in os.walk(KEXTS_PATH):
        for folder in dirs:
            if folder.endswith(".kext"):
                kext_path = os.path.join(root, folder)
                config_path = os.path.join(kext_path, "config.json")

                if os.path.exists(config_path):
                    #try:
                        with open(config_path, "r") as f:
                            config = json.load(f)
                            exec_rel_path = config.get("ExecutablePath", "")
                            if exec_rel_path:
                                exec_path = os.path.join(kext_path, exec_rel_path)
                                if os.path.isfile(exec_path):
                                    printout(f"[kext] Running: {folder}", verbose)
                                    if verbose:
                                        verbose1 = '1'
                                    else: 
                                        verbose1 = '0'
                                    subprocess.call(["python", exec_path, verbose1])
                                else:
                                    printout(f"[kext] Executable not found: {exec_path}", verbose)
                            else:
                                printout(f"[kext] {folder}/config.json Incorrectly Made.", verbose)
                    #except Exception as e:
                    #    printout(f"[kext] Error loading config for {folder}: {e}", verbose)
                else:
                    printout(f"[kext] config.json not found in {folder}", verbose)
        break  # Don't walk recursively into .kext contents
    if not os.path.exists(DRIVERS_PATH):
        printout("[driver] No drivers path found.", verbose)
        return

    for folder in os.listdir(DRIVERS_PATH):
        folder_path = os.path.join(DRIVERS_PATH, folder)
        if os.path.isdir(folder_path):
            expected_file = os.path.join(folder_path, folder)
            if os.path.isfile(expected_file):
                printout(f"[driver] Running: {folder}", verbose)
                subprocess.call(["python", expected_file, verbose])
            else:
                pass