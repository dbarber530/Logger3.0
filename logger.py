import yfinance as yf
import csv
import time
import os
from datetime import datetime
import pytz
import base64
import requests

# Ticker list (validated)
tickers = [
    'CALM', 'CRWV', 'NVTS', 'USVM', 'AAPL',
    'RXRX', 'SLNO', 'MNMD', 'SNTI', 'QQQ',
    'META', 'BABA', 'PLTR', 'AMD', 'GOOGL',
    'COIN', 'F', 'T', 'CVX', 'XOM',
    'NVO', 'LLY', 'SPY', 'VTI', 'IWM',
    'SOFI', 'TSLA', 'NVDA', 'MSFT', 'AMZN'
]

# Logging config
log_file = "data/log.csv"
log_interval = 60  # in seconds

# GitHub config (must be set as Railway environment variables)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

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
        with open(log_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Ticker', 'Price', 'Volume', 'Change (%)'])

def push_to_github():
    with open(log_file, "rb") as file:
        encoded_content = base64.b64encode(file.read()).decode('utf-8')

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{log_file}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # Get SHA of existing file if present
    response = requests.get(url, headers=headers)
    sha = response.json().get("sha") if response.status_code == 200 else None

    data = {
        "message": "Automated log update",
        "content": encoded_content,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha

    put_response = requests.put(url, json=data, headers=headers)
    if put_response.status_code in [200, 201]:
        print("✅ GitHub upload successful.")
    else:
        print(f"❌ GitHub upload failed: {put_response.json()}")

def run_logger():
    print("🧠 BarberBot Logger started.")
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
                        change_pct = round((latest["Close"] - latest["Open"]) / latest["Open"] * 100, 2)
                        rows.append([now, ticker, price, volume, change_pct])
                except Exception as e:
                    print(f"⚠️ {ticker} failed: {e}")
            with open(log_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
            print(f"✅ Logged {len(rows)} tickers.")
            push_to_github()
        else:
            print("⏸️ Market closed. Sleeping 10 minutes.")
            time.sleep(600)
        time.sleep(log_interval)

run_logger()
