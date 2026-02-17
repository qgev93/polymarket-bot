import requests
from config import TELEGRAM_BOT_TOKEN

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_message(chat_id: str, text: str) -> None:
    url = f"{API_BASE}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"sendMessage 실패: {data}")

def get_updates(offset: int):
    url = f"{API_BASE}/getUpdates"
    r = requests.get(url, params={"timeout": 10, "offset": offset}, timeout=15)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"getUpdates 실패: {data}")
    return data.get("result", [])
