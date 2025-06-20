import yfinance as yf
import csv
import time
from datetime import datetime
import pytz
import os
import requests

# ------------------ SETTINGS ------------------ #

tickers = [
    'CALM', 'CRWV', 'NVTS', 'USVM', 'AAPL',
    'RXRX', 'SLNO', 'MNMD', 'SNTI', 'QTT',
    'META', 'BABA', 'PLTR', 'AMD', 'GOOG',
    'COIN', 'F', 'T', 'CVX', 'XOM',
    'NIO', 'RIVN', 'TSLA', 'MSFT', 'AMZN',
    'DIS', 'ABNB', 'UBER', 'INTC', 'SBUX'
]

log_file = os.getenv("CSV_FILEPATH", "data/log.csv")
log_interval = 60  # seconds

github_token = os.getenv("GITHUB_TOKEN")
github_repo = os.getenv("GITHUB_REPO")
github_user = os.getenv("GITHUB_USERNAME")

# ------------------ FUNCTIONS ------------------ #

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
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Ticker", "Price", "Volume", "% Change"])

def push_to_github():
    try:
        url = f"https://api.github.com/repos/{github_repo}/contents/{log_file}"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Get the current SHA
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            sha = r.json()['sha']
        else:
            sha = None

        with open(log_file, "rb") as f:
            content = f.read()

        encoded_content = content.encode("base64") if hasattr(content, 'encode') else content.decode("latin1").encode("base64")

        data = {
            "message": "Automated log update",
            "content": encoded_content.decode('utf-8'),
            "branch": "main"
        }

        if sha:
            data["sha"] = sha

        response = requests.put(url, headers=headers, json=data)
        if response.status_code in [200, 201]:
            print("✅ GitHub push successful.")
        else:
            print(f"❌ GitHub push failed: {response.status_code} {response.text}")

    except Exception as e:
        print(f"❌ GitHub push error: {e}")

def run_logger():
    print("📉 BarberBot Logger started.")
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
                        change_pct = round(((latest["Close"] - latest["Open"]) / latest["Open"]) * 100, 2)
                        rows.append([now, ticker, price, volume, change_pct])
                except Exception as e:
                    print(f"⚠️ {ticker}: {e}")

            with open(log_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
            print(f"✅ Logged {len(rows)} ticker(s).")
            push_to_github()
        else:
            print("⏸️ Market closed. Sleeping for 10 minutes.")
            time.sleep(600)
        time.sleep(log_interval)

# ------------------ START ------------------ #
run_logger()
