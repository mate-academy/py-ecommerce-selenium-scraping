import psutil

# Iterate over all running processes
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    if proc.info['name'] == 'python.exe':
        print(f"PID: {proc.info['pid']}, Command Line: {proc.info['cmdline']}")