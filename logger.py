import yfinance as yf
import csv
import time
from datetime import datetime
import pytz
import os
import requests
import base64

tickers = [
    'CALM', 'CRWV', 'NVTS', 'USVM', 'AAPL',
    'RXRX', 'SLNO', 'NMMD', 'SNTI', 'QTT',
    'META', 'BABA', 'PLTR', 'AMD', 'GOOG',
    'COIN', 'F', 'T', 'CVX', 'XOM',
    'NVO', 'ABNB', 'NIO', 'RIVN', 'PFE',
    'DIS', 'SOFI', 'SHOP', 'WMT', 'INTC'
]

log_file = "data/log.csv"
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
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "Ticker", "Price", "Volume", "% Change"])

def push_to_github():
    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("GITHUB_USERNAME")
    repo = os.getenv("GITHUB_REPO")
    if not all([token, username, repo]):
        print("❌ Missing GitHub environment variables.")
        return

    api_url = f"https://api.github.com/repos/{repo}/contents/{log_file}"
    with open(log_file, "rb") as f:
        content = f.read()
        encoded = base64.b64encode(content).decode("utf-8")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    # Check if the file already exists to get SHA
    res = requests.get(api_url, headers=headers)
    if res.status_code == 200:
        sha = res.json()["sha"]
    else:
        sha = None

    payload = {
        "message": f"Automated log update {now}",
        "content": encoded,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(api_url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print("✅ GitHub push successful.")
    else:
        print(f"❌ GitHub push failed: {response.json()}")

def run_logger():
    print("🛰️ BarberBot Logger started.")
    init_log()
    while True:
        if is_market_open():
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows = []
            for ticker in tickers:
                try:
                    data = yf.download(ticker, period="1d", interval="1m")
                    if not data.empty:
                        latest = data.iloc[-1]
                        price = round(latest["Close"], 2)
                        volume = int(latest["Volume"])
                        change_pct = round(((latest["Close"] - data.iloc[0]["Open"]) / data.iloc[0]["Open"]) * 100, 2)
                        rows.append([now, ticker, price, volume, change_pct])
                except Exception as e:
                    print(f"⚠️ {ticker}: {e}")

            with open(log_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            print(f"✅ Logged {len(rows)} ticker(s) at {now}")
            push_to_github()
        else:
            print("⏸️ Market closed. Sleeping longer.")
            time.sleep(600)
        time.sleep(log_interval)

run_logger()
