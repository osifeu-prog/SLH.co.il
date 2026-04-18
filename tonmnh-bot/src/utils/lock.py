# utils/lock.py
import os
import sys
import subprocess
import atexit
import signal

def check_lock_and_create(lock_file):
    current_pid = os.getpid()
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                pid = f.read().strip()
            old_pid = int(pid)
            # Docker fix: if lock PID == our PID (both are 1 in Docker),
            # it's a stale lock from a previous container run
            if old_pid == current_pid:
                os.remove(lock_file)
                print(f"⚠️ Removed stale lock (same PID {pid}, likely Docker restart).")
            else:
                # Check if process is running (cross-platform)
                try:
                    os.kill(old_pid, 0)
                    is_running = True
                except (OSError, ValueError):
                    is_running = False
                if is_running:
                    print(f"❌ Bot already running (PID: {pid}). Exiting.")
                    sys.exit(1)
                else:
                    os.remove(lock_file)
                    print(f"⚠️ Removed stale lock file from PID {pid}.")
        except (ValueError, Exception) as e:
            print(f"⚠️ Error checking lock file: {e}. Removing and continuing.")
            try:
                os.remove(lock_file)
            except:
                pass
    with open(lock_file, 'w') as f:
        f.write(str(current_pid))
    print(f"🔒 Lock file created with PID: {current_pid}")

def remove_lock(lock_file):
    if os.path.exists(lock_file):
        os.remove(lock_file)
        print("🔓 Lock file removed.")

def setup_lock(lock_file):
    check_lock_and_create(lock_file)
    atexit.register(remove_lock, lock_file)
    def signal_handler(sig, frame):
        remove_lock(lock_file)
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
