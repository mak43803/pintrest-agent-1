import os
import shutil
import psutil

session_dir = r"C:\Users\mazzu\OneDrive\Desktop\pintrest ai agent\browser_session"
lock_files = [
    os.path.join(session_dir, "lockfile"),
    os.path.join(session_dir, "SingletonLock"),
    os.path.join(session_dir, "Default", "SingletonLock")
]

# Find any chrome processes that are using our user-data-dir
killed = 0
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['name'] == 'chrome.exe' or proc.info['name'] == 'chromium.exe':
            cmdline = proc.info['cmdline']
            if cmdline:
                cmdline_str = " ".join(cmdline).lower()
                if "pintrest ai agent" in cmdline_str or "browser_session" in cmdline_str:
                    print(f"Killing chrome process {proc.info['pid']} holding the lock...")
                    proc.kill()
                    killed += 1
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

print(f"Killed {killed} chrome processes using browser_session.")

# Try to delete lock files
for lock in lock_files:
    if os.path.exists(lock):
        try:
            os.remove(lock)
            print(f"Deleted lock file: {lock}")
        except Exception as e:
            print(f"Failed to delete lock file {lock}: {e}")
            
# Also check if Default directory has other lock-like files
if os.path.exists(session_dir):
    for root, dirs, files in os.walk(session_dir):
        for file in files:
            if "lock" in file.lower() or "singleton" in file.lower():
                filepath = os.path.join(root, file)
                try:
                    os.remove(filepath)
                    print(f"Deleted nested lock file: {filepath}")
                except Exception as e:
                    print(f"Failed to delete nested lock file {filepath}: {e}")
