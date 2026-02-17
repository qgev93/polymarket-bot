import time
import traceback

from config import TELEGRAM_CHAT_ID, MODE, TELEGRAM_BOT_TOKEN
from telegram_client import send_message, get_updates
from paper_broker import PaperBroker
from strategy import decide
from risk import apply_risk

STATE = {
    "paused": False,
    "panic": False,
    "offset": 0,          # getUpdates offset
    "last_heartbeat": 0,  # 상태용
}

def must_have_env():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("환경변수 필요: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")

def fmt_positions(broker) -> str:
    try:
        pos = broker.get_positions()
        return str(pos)
    except Exception as e:
        return f"(positions error: {e})"

def handle_command(text: str, broker):
    t = (text or "").strip()

    if t == "/status":
        bal = broker.get_balance()
        pos = fmt_positions(broker)
        msg = (
            "🤖 STATUS\n"
            f"- MODE: {MODE}\n"
            f"- paused: {STATE['paused']}\n"
            f"- panic: {STATE['panic']}\n"
            f"- balance: {bal:.2f}\n"
            f"- positions: {pos}\n"
        )
        send_message(TELEGRAM_CHAT_ID, msg)
        return

    if t == "/pause":
        STATE["paused"] = True
        send_message(TELEGRAM_CHAT_ID, "⏸️ PAUSE 됨 (엔진 멈춤)")
        return

    if t == "/resume":
        STATE["panic"] = False
        STATE["paused"] = False
        send_message(TELEGRAM_CHAT_ID, "▶️ RESUME 됨 (엔진 재개)")
        return

    if t == "/panic":
        STATE["panic"] = True
        STATE["paused"] = True
        send_message(TELEGRAM_CHAT_ID, "🛑 PANIC! 긴급정지 (paused=true)")
        return

    # 기타 텍스트
    send_message(
        TELEGRAM_CHAT_ID,
        "명령어:\n/status\n/pause\n/resume\n/panic\n"
    )

def poll_telegram(broker):
    """
    텔레그램 업데이트를 읽고 명령 처리
    """
    updates = get_updates(STATE["offset"] + 1)
    for u in updates:
        update_id = u.get("update_id", 0)
        STATE["offset"] = max(STATE["offset"], update_id)

        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat") or {}
        chat_id = str(chat.get("id", ""))

        # 본인 chat만 받기 (보안)
        if chat_id != TELEGRAM_CHAT_ID:
            continue

        text = msg.get("text", "")
        if text:
            handle_command(text, broker)

def engine_step(broker):
    """
    매 루프마다 시장을 훑고, 전략->리스크->주문(페이퍼) 실행
    """
    markets = broker.get_markets()

    for m in markets:
        d = decide(m)
        if not d.order:
            continue

        bal = broker.get_balance()
        rr = apply_risk(d.order, bal)
        if not rr.ok:
            send_message(TELEGRAM_CHAT_ID, f"⚠️ 리스크 컷: {rr.reason}")
            continue

        fill = broker.place_order(rr.adjusted_order)
        send_message(
            TELEGRAM_CHAT_ID,
            f"✅ 페이퍼 체결: {fill.order.market_id} {fill.order.side} "
            f"size={fill.filled_size:.4f} price={fill.avg_price:.4f} "
            f"bal={broker.get_balance():.2f}\n이유: {d.reason}"
        )

def main():
    must_have_env()

    broker = PaperBroker(starting_balance=50.0)

    send_message(
        TELEGRAM_CHAT_ID,
        "🤖 통합 엔진 시작!\n"
        "명령어: /status /pause /resume /panic\n"
        f"(MODE={MODE}, PAPER broker)\n"
        "※ 지금은 VPS에서 실행 중일 때만 응답함"
    )

    # 루프 주기(너무 빡세게 돌지 말자)
    TELEGRAM_POLL_SEC = 2
    ENGINE_TICK_SEC = 10

    last_engine = 0

    while True:
        try:
            # 1) 텔레그램 명령 처리(자주)
            poll_telegram(broker)

            # 2) 엔진은 일정 주기마다 실행
            now = time.time()
            if not STATE["paused"] and not STATE["panic"]:
                if now - last_engine >= ENGINE_TICK_SEC:
                    engine_step(broker)
                    last_engine = now

            time.sleep(TELEGRAM_POLL_SEC)

        except Exception as e:
            # 에러는 텔레그램으로 쏘고, 잠깐 쉬었다가 재시도
            err = f"⚠️ 에러: {e}\n{traceback.format_exc()[:1500]}"
            try:
                send_message(TELEGRAM_CHAT_ID, err)
            except Exception:
                pass
            time.sleep(5)

if __name__ == "__main__":
    main()
