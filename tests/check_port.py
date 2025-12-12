import subprocess
import re

def find_pid():
    try:
        output = subprocess.check_output("netstat -ano", shell=True).decode(errors='ignore')
        for line in output.splitlines():
            if ":8009" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                with open("debug_output.txt", "w") as f:
                    f.write(f"PID:{pid}")
                return
        with open("debug_output.txt", "w") as f:
            f.write("PID:NOT_FOUND")
    except Exception as e:
        with open("debug_output.txt", "w") as f:
            f.write(f"ERROR:{str(e)}")

if __name__ == "__main__":
    find_pid()
