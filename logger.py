import yfinance as yf
import csv
import time
from datetime import datetime
import pytz
import os
import base64
import requests

tickers = [
    'CALM', 'CRVW', 'NVTS', 'USVM', 'ACDC',
    'RXRX', 'SLNO', 'NMMD', 'SNTI', 'QTT',
    'META', 'BABA', 'PLTR', 'AMD', 'GOOG',
    'COIN', 'CRWD', 'CVX', 'XOM', 'NVO'
]

log_file = os.getenv("CSV_FILEPATH", "data/log.csv")
log_interval = 60  # seconds

def is_market_open():
    now_utc = datetime.now(pytz.utc)
    eastern = pytz.timezone("US/Eastern")
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
            writer.writerow(["Timestamp", "Ticker", "Price", "Volume", "Change %"])

def push_to_github():
    print("📡 Uploading log to GitHub via API...")

    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO", "dbarber530/Logger3.0")
    path = "data/log.csv"

    with open(log_file, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")

    url = f"https://api.github.com/repos/{repo}/contents/{path}"

    # Get SHA of existing file (if it exists)
    r = requests.get(url, headers={"Authorization": f"token {token}"})
    sha = r.json().get("sha") if r.status_code == 200 else None

    payload = {
        "message": "Automated log update",
        "content": content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    res = requests.put(url, json=payload, headers={"Authorization": f"token {token}"})
    if res.status_code in [200, 201]:
        print("✅ GitHub upload successful.")
    else:
        print(f"❌ GitHub upload failed. Status: {res.status_code}")
        print(res.json())

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
                        change_pct = round((latest["Close"] - data["Open"].iloc[0]) / data["Open"].iloc[0] * 100, 2)
                        rows.append([now, ticker, price, volume, change_pct])
                except Exception as e:
                    print(f"⚠️ {ticker}: {e}")
            with open(log_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            print(f"✅ Logged {len(rows)} ticker(s).")
            push_to_github()
        else:
            print("⏸️ Market closed. Sleeping 10 min.")
            time.sleep(600)
        time.sleep(log_interval)

run_logger()
