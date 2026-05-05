import requests
import time
import json
import os
from datetime import datetime
from telegram import Bot

# =========================
# ⚙️ CONFIG
# =========================
# يقرأ من البيئة، وإذا غير موجود يستعمل fallback
TOKEN = os.getenv("TOKEN") or "8145144025:AAGeHljihv0JELuJpmxCo4J18bBXMH3GeI8"
CHAT_ID = "6291959044"

bot = Bot(token=TOKEN)

URL = "https://adhahi.dz/api/v1/public/wilaya-quotas"
STATE_FILE = "state.json"


# =========================
# ⏱️ TIME (ثواني فقط)
# =========================
def now_time():
    return datetime.now().strftime("%H:%M:%S")


# =========================
# 💾 STATE
# =========================
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except:
        pass


# =========================
# 🌐 FETCH DATA (retry)
# =========================
def fetch_data():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://adhahi.dz/",
        "Accept": "application/json"
    }

    for _ in range(3):
        try:
            r = requests.get(URL, headers=headers, timeout=30)
            if r.status_code == 200:
                return r.json()
        except:
            print("⚠️ اتصال ضعيف مع الموقع...")
            time.sleep(2)

    return []


# =========================
# 📩 SEND SAFE
# =========================
def send_message(text):
    try:
        bot.send_message(CHAT_ID, text)
    except:
        print("⚠️ فشل إرسال Telegram")


# =========================
# 🚀 MAIN LOOP
# =========================
def main():
    old_state = load_state()

    print("🚀 BOT STARTED")

    while True:
        data = fetch_data()

        if not data:
            print("⚠️ فشل جلب البيانات")
            time.sleep(5)
            continue

        new_state = {}
        open_count = 0
        closed_count = 0

        for w in data:
            name = w.get("wilayaNameAr")
            status = w.get("available")

            if not name:
                continue

            new_state[name] = status

            if status:
                open_count += 1
            else:
                closed_count += 1

            # 🔔 إشعار عند التغيير فقط
            if name in old_state and old_state[name] != status:
                t = now_time()

                if name == "تلمسان":
                    if status:
                        send_message(f"🚨🚨 تلمسان فتحت\n⏰ {t}")
                    else:
                        send_message(f"🔴 تلمسان أغلقت\n⏰ {t}")
                else:
                    if status:
                        send_message(f"🟢 {name} فتحت\n⏰ {t}")
                    else:
                        send_message(f"🔴 {name} أغلقت\n⏰ {t}")

        save_state(new_state)
        old_state = new_state

        print(f"{now_time()} | 🟢 {open_count} | 🔴 {closed_count}")

        time.sleep(3)


# =========================
# ▶️ START
# =========================
if __name__ == "__main__":
    main()
