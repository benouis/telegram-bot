import time
import requests
import json
from datetime import datetime
import threading
import os

TOKEN = "8145144025:AAGeHljihv0JELuJpmxCo4J18bBXMH3GeI8"
CHAT_ID = "6291959044"

API_URL = "https://adhahi.dz/api/v1/public/wilaya-quotas"

TARGET_WILAYA = "تلمسان"

STATE_FILE = "state.json"

current_state = {}
initialized = False


# =========================
# 💾 حفظ الحالة
# =========================
def save_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# =========================
# 📂 تحميل الحالة
# =========================
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# =========================
# 📩 إرسال رسالة
# =========================
def send(msg):
    keyboard = {
        "keyboard": [
            ["🟢 المفتوحة", "🔴 المغلقة"],
            ["📊 مراجعة دورية", "📍 ولايتي"]
        ],
        "resize_keyboard": True
    }

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "reply_markup": keyboard
            },
            timeout=5
        )
    except:
        pass


# =========================
# 🔥 MONITOR
# =========================
def monitor():
    global current_state, initialized

    print("🚀 SMART TRACKING STARTED")

    current_state = load_state()

    if current_state:
        initialized = True
        print("💾 تم تحميل الحالة السابقة")
    else:
        print("⚠️ لا توجد حالة محفوظة")

    fast_mode_cycles = 0

    while True:
        sleep_time = 3

        try:
            res = requests.get(API_URL, timeout=5)

            if res.status_code != 200:
                time.sleep(3)
                continue

            data = res.json()

            new_state = {}

            for item in data:
                name = item.get("wilayaNameAr", "").strip()
                available = item.get("available", False)

                if name:
                    new_state[name] = available

            if not new_state:
                time.sleep(3)
                continue

            now = datetime.now().strftime("%H:%M:%S")

            if not initialized:
                current_state = new_state
                save_state(current_state)
                initialized = True
                print("✅ INITIALIZED + SAVED")
                time.sleep(2)
                continue

            changed = False

            for wilaya, new_val in new_state.items():
                old_val = current_state.get(wilaya)

                # 🟢 فتح
                if old_val is False and new_val is True:

                    if wilaya == TARGET_WILAYA:
                        send(f"🚨 {wilaya} فتحت\n⏰ {now}")
                    else:
                        send(f"🟢 {wilaya} فتحت")

                    changed = True

                # 🔴 غلق
                elif old_val is True and new_val is False:

                    if wilaya == TARGET_WILAYA:
                        send(f"⚠️ {wilaya} أغلقت\n⏰ {now}")
                    else:
                        send(f"🔴 {wilaya} أغلقت")

                    changed = True

            # 🔥 التعديل المهم (Smart Alert Pro)
            current_state = new_state
            save_state(current_state)

            # Smart Speed
            if changed:
                fast_mode_cycles = 8

            if fast_mode_cycles > 0:
                sleep_time = 2
                fast_mode_cycles -= 1
            else:
                sleep_time = 3

        except Exception as e:
            print("ERROR:", e)
            sleep_time = 5

        time.sleep(sleep_time)


# =========================
# 🤖 TELEGRAM
# =========================
def telegram_listener():
    last_update_id = 0

    requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset=-1")

    send("⚡ البوت يعمل الآن (Smart Pro)")

    while True:
        try:
            res = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                timeout=5
            )

            data = res.json()

            if not data.get("ok"):
                continue

            for update in data["result"]:
                if update["update_id"] > last_update_id:
                    last_update_id = update["update_id"]

                    if "message" in update:
                        text = update["message"].get("text", "")

                        opened = [w for w, v in current_state.items() if v]
                        closed = [w for w, v in current_state.items() if not v]

                        if text == "🟢 المفتوحة":
                            send("🟢 المفتوحة:\n" + "\n".join([f"✔️ {w}" for w in opened]))

                        elif text == "🔴 المغلقة":
                            send("🔴 المغلقة:\n" + "\n".join([f"❌ {w}" for w in closed]))

                        elif text == "📊 مراجعة دورية":
                            now = datetime.now().strftime("%H:%M:%S")

                            msg = f"📊 {now}\n"
                            msg += f"🟢 {len(opened)} | 🔴 {len(closed)}\n\n"

                            msg += "🟢 المفتوحة:\n"
                            msg += "\n".join([f"✔️ {w}" for w in opened])

                            msg += "\n\n🔴 المغلقة:\n"
                            msg += "\n".join([f"❌ {w}" for w in closed])

                            send(msg)

                        elif text == "📍 ولايتي":
                            if TARGET_WILAYA in current_state and current_state[TARGET_WILAYA]:
                                send(f"📍 {TARGET_WILAYA}: ✔️ مفتوحة")
                            else:
                                send(f"📍 {TARGET_WILAYA}: ❌ مغلقة")

        except Exception as e:
            print("ERROR TG:", e)

        time.sleep(1)


# =========================
# 🚀 START
# =========================
threading.Thread(target=monitor).start()
threading.Thread(target=telegram_listener).start()