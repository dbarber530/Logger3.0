import yfinance as yf
import csv
import time
from datetime import datetime
import pytz
import os
import subprocess

tickers = [
    'CALM', 'CRWV', 'NVTS', 'USVM', 'AAPL', 'RXRX', 'SLNO', 'NMMD', 'SNTI', 'QQQ',
    'META', 'BABA', 'PLTR', 'AMD', 'GOOGL', 'COIN', 'F', 'T', 'CVX', 'XOM', 'NVDA'
]

log_file = os.getenv("CSV_FILEPATH", "data/market_log.csv")
log_interval = 60  # in seconds

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
    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    if not os.path.exists(log_file):
        with open(log_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Ticker", "Price", "Volume", "Change %"])

def push_to_github():
    try:
        subprocess.run([
            "git", "add", "."
        ], check=True)
        subprocess.run([
            "git", "commit", "-m", f"Auto log {datetime.now()}"
        ], check=True)
        subprocess.run([
            "git", "push"
        ], check=True)
        print("✅ GitHub push successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ GitHub push failed: {e}")

def run_logger():
    print("🪵 BarberBot Logger started.")
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
                    print(f"⚠️ {ticker}: {e}")
            with open(log_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            print(f"✅ Logged {len(rows)} ticker(s).")
            push_to_github()
        else:
            print("⏸️ Market closed. Sleeping 10 minutes.")
            time.sleep(600)
        time.sleep(log_interval)

run_logger()
