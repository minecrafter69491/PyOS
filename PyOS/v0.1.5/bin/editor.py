import sys
import os

def edit_file(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []

    print(f"[editor] Editing {path}. Enter ':w' to save and quit, ':q' to quit without saving.")

    while True:
        for i, line in enumerate(lines):
            print(f"{i+1:>3}: {line.rstrip()}")

        cmd = input("> ")
        if cmd == ":q":
            print("[editor] Quit without saving.")
            return
        elif cmd == ":w":
            with open(path, 'w') as f:
                f.writelines(lines)
            print("[editor] File saved.")
            return
        elif cmd.startswith("a "):  # append
            lines.append(cmd[2:] + '\n')
        elif cmd.startswith("d "):  # delete line
            try:
                lineno = int(cmd[2:]) - 1
                if 0 <= lineno < len(lines):
                    lines.pop(lineno)
            except:
                print("[editor] Invalid line number.")
        elif cmd.startswith("e "):  # edit line
            try:
                parts = cmd.split(' ', 2)
                lineno = int(parts[1]) - 1
                if 0 <= lineno < len(lines):
                    lines[lineno] = parts[2] + '\n'
            except:
                print("[editor] Usage: e <line> <new text>")
        else:
            print("[editor] Unknown command. Use a <text>, d <line>, e <line> <text>, :w, :q")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: editor.py <file>")
        sys.exit(1)
    edit_file(sys.argv[1])
