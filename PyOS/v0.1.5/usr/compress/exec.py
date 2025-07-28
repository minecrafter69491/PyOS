import sys
import os
sys.path.append(os.path.join(os.getcwd(), "bin"))  # Add /bin to import path

def frun():
    ...
import os
import zipfile
import shutil

def zip_directory(source_dir, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, source_dir)
                zipf.write(abs_path, rel_path)

def main(args):
    path = input("Enter the path to files and folders to compress(full path from /): ")
    script_dir = os.environ.get('ROOTFS')
    kernel_dir = os.path.join(script_dir, path)

    if not os.path.exists(kernel_dir) or not os.path.isdir(kernel_dir):
        print(f"[error] directory '{path}' not found.")
        return

    # Project root: parent of the script directory
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    filename = input("Enter your prefered filename for you compressed archive: ")
    output_zip = os.path.join(project_root, f"{filename}.zip")

    print(f"[info] Compressing {path} to {output_zip}...")

    zip_directory(kernel_dir, output_zip)

    print("[done] kernel.zip created at project root.")
