import requests
import time
import json
import os
from telegram import Bot

# 🔴 عدّل فقط هذين
import os
TOKEN = os.getenv("8145144025:AAGeHljihv0JELuJpmxCo4J18bBXMH3GeI8")
CHAT_ID = "6291959044"

bot = Bot(token=TOKEN)

URL = "https://adhahi.dz/api/v1/public/wilaya-quotas"
STATE_FILE = "state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def fetch_data():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://adhahi.dz/",
        "Accept": "application/json"
    }

    for _ in range(3):
        try:
            r = requests.get(URL, headers=headers, timeout=10, verify=False)
            return r.json()
        except Exception as e:
            print("ERROR:", e)
            time.sleep(2)

    return []


old_state = load_state()

while True:
    data = fetch_data()

    if not data:
        print("⚠️ فشل جلب البيانات")
        time.sleep(10)
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

        # 🔔 تنبيه ذكي (فقط عند التغيير)
        if name in old_state and old_state[name] != status:
            if name == "تلمسان":
                if status:
                    bot.send_message(CHAT_ID, "🚨🚨 تلمسان فتحت الآن 🔔")
                else:
                    bot.send_message(CHAT_ID, "🔴 تلمسان أغلقت")
            else:
                if status:
                    bot.send_message(CHAT_ID, f"🟢 {name} فتحت")
                else:
                    bot.send_message(CHAT_ID, f"🔴 {name} أغلقت")

    save_state(new_state)
    old_state = new_state

    print(f"🟢 {open_count} | 🔴 {closed_count}")

    time.sleep(5)
