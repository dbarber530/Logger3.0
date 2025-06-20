import yfinance as yf
import csv
import time
from datetime import datetime
import pytz
import os
import requests
import base64
import json

tickers = [
    'CALM', 'CRWV', 'NVTS', 'USVM', 'AAPL',
    'RXRX', 'SLNO', 'MNMD', 'SNTI', 'QQQ',
    'META', 'BABA', 'PLTR', 'AMD', 'GOOG',
    'COIN', 'F', 'T', 'CVX', 'XOM'
]
]

log_file = os.getenv("CSV_FILEPATH", "data/log.csv")
log_interval = 60  # seconds

def is_market_open():
    now_utc = datetime.now(pytz.utc)
    eastern = pytz.timezone('US/Eastern')
    now_et = now_utc.astimezone(eastern)

    if now_et.weekday() >= 5:
        return False

    open_et = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    close_et = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_et <= now_et <= close_et

def init_log():
    if not os.path.exists(log_file):
        with open(log_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Ticker', 'Price', 'Volume', 'Change %'])

def push_to_github():
    try:
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPO")
        username = os.getenv("GITHUB_USERNAME")
        file_path = "data/log.csv"
        api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

        with open(file_path, "rb") as file:
            content = base64.b64encode(file.read()).decode("utf-8")

        res = requests.get(api_url, headers={"Authorization": f"Bearer {token}"})
        sha = res.json().get("sha") if res.status_code == 200 else None

        payload = {
            "message": "🔁 Automated log update",
            "content": content,
            "branch": "main",
            "committer": {
                "name": username,
                "email": f"{username}@users.noreply.github.com"
            }
        }

        if sha:
            payload["sha"] = sha

        push_res = requests.put(api_url, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }, data=json.dumps(payload))

        if push_res.status_code in [200, 201]:
            print("✅ GitHub push successful.")
        else:
            print(f"❌ GitHub push failed: {push_res.status_code}, {push_res.text}")

    except Exception as e:
        print(f"❌ Push error: {e}")

def run_logger():
    print("📉 BarberBot Logger started.")
    init_log()
    while True:
        if is_market_open():
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            rows = []
            for ticker in tickers:
                try:
                    data = yf.download(ticker, period="1d", interval="1m")
                    if not data.empty:
                        latest = data.iloc[-1]
                        price = round(latest["Close"], 2)
                        volume = int(latest["Volume"])
                        change_pct = round(((latest["Close"] - data["Open"][0]) / data["Open"][0]) * 100, 2)
                        rows.append([now, ticker, price, volume, change_pct])
                except Exception as e:
                    print(f"⚠️ {ticker}: {e}")

            with open(log_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            print(f"✅ Logged {len(rows)} ticker(s).")
            push_to_github()
        else:
            print("⏸️ Market closed. Sleeping for 10 minutes.")
            time.sleep(600)

        time.sleep(log_interval)

run_logger()
