import psutil
import os
import time

# Kill all watchdog.py and main.py Python processes except ourselves (inspect_db.py / current process)
current_pid = os.getpid()
killed_python = 0

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['pid'] == current_pid:
            continue
        if proc.info['name'] == 'python.exe':
            cmdline = proc.info['cmdline']
            if cmdline:
                cmdline_str = " ".join(cmdline).lower()
                if "watchdog.py" in cmdline_str or "main.py" in cmdline_str:
                    print(f"Killing agent python process: PID {proc.info['pid']} ({cmdline_str})")
                    proc.kill()
                    killed_python += 1
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

print(f"Killed {killed_python} agent python processes.")

# Sleep a bit to let processes die
time.sleep(2)

# Kill any chrome processes using browser_session
killed_chrome = 0
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['name'] in ['chrome.exe', 'chromium.exe']:
            cmdline = proc.info['cmdline']
            if cmdline:
                cmdline_str = " ".join(cmdline).lower()
                if "pintrest ai agent" in cmdline_str or "browser_session" in cmdline_str:
                    print(f"Killing chrome process: PID {proc.info['pid']}")
                    proc.kill()
                    killed_chrome += 1
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

print(f"Killed {killed_chrome} chrome processes.")

# Clean up lock files
session_dir = r"C:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\browser_session"
lock_files = [
    os.path.join(session_dir, "lockfile"),
    os.path.join(session_dir, "SingletonLock"),
    os.path.join(session_dir, "Default", "LOCK")
]

for lock in lock_files:
    if os.path.exists(lock):
        try:
            os.remove(lock)
            print(f"Deleted lock file: {lock}")
        except Exception as e:
            print(f"Failed to delete lock file {lock}: {e}")

# Check recursively for any other LOCK files
if os.path.exists(session_dir):
    for root, dirs, files in os.walk(session_dir):
        for file in files:
            if file.upper() == "LOCK" or "SINGLETONLOCK" in file.upper():
                filepath = os.path.join(root, file)
                try:
                    os.remove(filepath)
                    print(f"Deleted nested lock file: {filepath}")
                except Exception as e:
                    pass
