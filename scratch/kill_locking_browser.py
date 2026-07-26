import subprocess
import os
import signal
import sys

print("Searching for processes locking browser_session...")

try:
    import psutil
except ImportError:
    print("psutil not installed. Installing psutil...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

killed = 0
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = proc.info['cmdline']
        if cmdline and any('browser_session' in arg for arg in cmdline):
            pid = proc.info['pid']
            print(f"Found locking process: PID {pid} ({proc.info['name']}) -> {' '.join(cmdline)}")
            proc.kill()
            killed += 1
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

print(f"Done. Killed {killed} processes.")
