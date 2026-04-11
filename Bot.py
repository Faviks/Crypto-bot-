import time
import requests
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID        = os.environ.get("CHAT_ID")
SPIKE_PERCENT  = 0.5
CHECK_INTERVAL = 60
WINDOW_MINUTES = 5

price_history = {}

def get_all_prices():
    url = "https://api.binance.com/api/v3/ticker/price"
    headers = {"X-Forwarded-For": "203.0.113.1"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return {item["symbol"]: float(item["price"]) for item in r.json()}

def send_alert(symbol, old_price, new_price, pct_change):
    direction = "🚀" if pct_change > 0 else "🔻"
    msg = (
        f"{direction} *{symbol} spike detected!*\n"
        f"Change: `{pct_change:+.2f}%`\n"
        f"Old: `${old_price:.6f}`  →  New: `${new_price:.6f}`\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })

def check_spikes():
    now = time.time()
    cutoff = now - (WINDOW_MINUTES * 60)
    prices = get_all_prices()

    for symbol, current_price in prices.items():
        if current_price == 0:
            continue
        history = price_history.setdefault(symbol, [])
        history[:] = [(t, p) for t, p in history if t >= cutoff]

        if history:
            baseline_price = history[0][1]
            if baseline_price == 0:
                history.append((now, current_price))
                continue
            pct_change = ((current_price - baseline_price) / baseline_price) * 100

            if abs(pct_change) >= SPIKE_PERCENT:
                send_alert(symbol, baseline_price, current_price, pct_change)
                history.clear()

        history.append((now, current_price))

def main():
    print("Bot started. Monitoring all Binance pairs...")
    while True:
        try:
            check_spikes()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
