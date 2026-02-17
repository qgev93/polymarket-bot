import os
import time
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

STATE = {
    "paused": False,
    "panic": False,
    "last_update_id": 0,
}

def must_have_env():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("환경변수 필요: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")

def send_message(text, chat_id=None):
    chat_id = chat_id or TELEGRAM_CHAT_ID
    url = f"{API_BASE}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def get_updates(offset):
    url = f"{API_BASE}/getUpdates"
    params = {"timeout": 10, "offset": offset}
    r = requests.get(url, params=params)
    data = r.json()
    return data.get("result", [])

def handle_command(text, chat_id):
    t = text.strip()

    if t == "/status":
        send_message(
            f"🤖 상태\npaused: {STATE['paused']}\npanic: {STATE['panic']}",
            chat_id
        )
        return

    if t == "/pause":
        STATE["paused"] = True
        send_message("⏸️ 일시정지 완료", chat_id)
        return

    if t == "/resume":
        STATE["paused"] = False
        STATE["panic"] = False
        send_message("▶️ 재개 완료", chat_id)
        return

    if t == "/panic":
        STATE["panic"] = True
        STATE["paused"] = True
        send_message("🛑 PANIC! 긴급정지", chat_id)
        return

    send_message("명령어: /status /pause /resume /panic", chat_id)

def main():
    must_have_env()
    send_message("🚀 봇 시작됨. /status 입력해봐")

    offset = STATE["last_update_id"] + 1

    while True:
        updates = get_updates(offset)

        for u in updates:
            update_id = u.get("update_id", 0)
            offset = max(offset, update_id + 1)

            msg = u.get("message", {})
            chat = msg.get("chat", {})
            chat_id = str(chat.get("id", ""))

            if chat_id != TELEGRAM_CHAT_ID:
                continue

            text = msg.get("text", "")
            if text:
                handle_command(text, chat_id)

        time.sleep(3)

if __name__ == "__main__":
    main()
