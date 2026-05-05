import requests
import time
import json
import os
from datetime import datetime
from telegram import Bot

# =========================
# ⚙️ CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = "6291959044"

bot = Bot(token=TOKEN)

URL = "https://adhahi.dz/api/v1/public/wilaya-quotas"
STATE_FILE = "state.json"


# =========================
# ⏱️ TIME (دقة عالية)
# =========================
def now_time():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


# =========================
# 💾 STATE
# =========================
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


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
            r = requests.get(URL, headers=headers, timeout=15)
            return r.json()
        except Exception:
            print("⚠️ اتصال ضعيف...")
            time.sleep(2)

    return []


# =========================
# 🚀 MAIN LOOP (Railway compatible)
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

            # 🔔 إشعار عند التغيير
            if name in old_state and old_state[name] != status:
                t = now_time()

                try:
                    if name == "تلمسان":
                        if status:
                            bot.send_message(CHAT_ID, f"🚨🚨 تلمسان فتحت\n⏰ {t}")
                        else:
                            bot.send_message(CHAT_ID, f"🔴 تلمسان أغلقت\n⏰ {t}")
                    else:
                        if status:
                            bot.send_message(CHAT_ID, f"🟢 {name} فتحت\n⏰ {t}")
                        else:
                            bot.send_message(CHAT_ID, f"🔴 {name} أغلقت\n⏰ {t}")
                except Exception:
                    print("⚠️ فشل إرسال Telegram")

        save_state(new_state)
        old_state = new_state

        print(f"{now_time()} | 🟢 {open_count} | 🔴 {closed_count}")

        time.sleep(3)


# =========================
# ▶️ START
# =========================
if __name__ == "__main__":
    main()
