import yfinance as yf
import csv
import time
import os
from datetime import datetime
import pytz
import base64
import requests

# ✅ VERIFIED TICKERS
tickers = [
    'CRWV', 'CALM', 'NVTS', 'USVM', 'AAPL', 'NVDA', 'TSLA', 'SPY',
    'RXRX', 'SLNO', 'MNMD', 'SNTI', 'QQQ', 'DIA', 'MSFT', 'AMZN',
    'META', 'BABA', 'PLTR', 'AMD', 'GOOG', 'NFLX', 'SHOP', 'SOFI',
    'COIN', 'FORD', 'T', 'CVX', 'XOM', 'NIO'
]

log_file = "data/log.csv"
log_interval = 60  # seconds

def is_market_open():
    now_utc = datetime.utcnow()
    eastern = pytz.timezone('US/Eastern')
    now_et = now_utc.replace(tzinfo=pytz.utc).astimezone(eastern)
    if now_et.weekday() >= 5:
        return False
    open_et = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    close_et = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_et <= now_et <= close_et

def init_log():
    try:
        with open(log_file, mode='x', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Ticker', 'Price', 'Change %', 'Volume'])
    except FileExistsError:
        pass

def upload_to_github(token, username, repo, file_path, commit_message):
    """Upload or update a file in a GitHub repository using the GitHub API."""
    api_url = f"https://api.github.com/repos/{username}/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        with open(file_path, "rb") as f:
            content = f.read()
        b64_content = base64.b64encode(content).decode("utf-8")

        get_resp = requests.get(api_url, headers=headers)
        sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

        data = {
            "message": commit_message,
            "content": b64_content,
            "branch": "main"
        }
        if sha:
            data["sha"] = sha

        put_resp = requests.put(api_url, headers=headers, json=data)
        if put_resp.status_code in [200, 201]:
            print("✅ Log pushed to GitHub successfully.")
        else:
            print("❌ GitHub push failed:", put_resp.json())
    except Exception as e:
        print("❌ GitHub upload error:", str(e))

def run_logger():
    print("📡 BarberBot Logger started.")
    init_log()
    while True:
        if is_market_open():
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            rows = []
            for ticker in tickers:
                try:
                    data = yf.Ticker(ticker).history(period='1d', interval='1m')
                    if not data.empty:
                        latest = data.iloc[-1]
                        price = round(latest['Close'], 2)
                        volume = int(latest['Volume'])
                        change_pct = round(((latest['Close'] - latest['Open']) / latest['Open']) * 100, 2)
                        rows.append([now, ticker, price, change_pct, volume])
                except Exception as e:
                    print(f"⚠️ {ticker}: {e}")
            with open(log_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            print(f"✅ Logged {len(rows)} tickers at {now}")

            # 🔁 GitHub Push
            upload_to_github(
                token=os.getenv("GITHUB_TOKEN"),
                username=os.getenv("GITHUB_USERNAME"),
                repo=os.getenv("GITHUB_REPO"),
                file_path=log_file,
                commit_message=f"Automated log update {now}"
            )
        else:
            print("⏸️ Market closed. Sleeping 10 minutes.")
            time.sleep(600)
        time.sleep(log_interval)

# ⏯️ Start logger
run_logger()
