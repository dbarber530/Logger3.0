import yfinance as yf
import csv, time, os, base64, requests
from datetime import datetime
import pytz

tickers = [
    'CRWV', 'NVTS', 'USVM', 'AAPL', 'RXRX',
    'SLNO', 'MNMD', 'SNTI', 'QQQ', 'META',
    'BABA', 'PLTR', 'AMD', 'GOOG', 'COIN',
    'F', 'T', 'CVX', 'XOM'
]

log_file = os.getenv("CSV_FILEPATH", "data/log.csv")
log_interval = 60  # seconds

def is_market_open():
    now = datetime.now(pytz.utc).astimezone(pytz.timezone("US/Eastern"))
    if now.weekday() >= 5:
        return False
    return now.replace(hour=9, minute=30, second=0, microsecond=0) <= now <= now.replace(hour=16, minute=0, second=0, microsecond=0)

def init_log():
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    if not os.path.exists(log_file):
        with open(log_file, "w", newline="") as f:
            csv.writer(f).writerow(["Timestamp","Ticker","Price","Volume","Change %"])

def push_to_github():
    print("📡 Uploading log to GitHub...")
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO", "dbarber530/Logger3.0")
    path = "data/log.csv"
    with open(log_file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    r = requests.get(url, headers={"Authorization": f"token {token}"})
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "Update log", "content": data, "branch": "main"}
    if sha:
        payload["sha"] = sha
    resp = requests.put(url, json=payload, headers={"Authorization": f"token {token}"})
    print("✅ GitHub upload successful." if resp.status_code in [200, 201] else f"❌ Upload failed: {resp.status_code}")

def run_logger():
    print("🛰️ BarberBot Logger started.")
    init_log()
    while True:
        if is_market_open():
            now = datetime.now(pytz.utc).astimezone(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S")
            rows = []
            for t in tickers:
                try:
                    df = yf.download(t, period="1d", interval="1m")
                    if not df.empty:
                        close, vol, openp = df["Close"].iloc[-1], int(df["Volume"].iloc[-1]), df["Open"].iloc[0]
                        change = round((close - openp)/openp * 100, 2)
                        rows.append([now, t, close, vol, change])
                except Exception as e:
                    print(f"⚠️ {t}: {e}")
            with open(log_file, "a", newline="") as f:
                csv.writer(f).writerows(rows)
            print(f"✅ Logged {len(rows)} tickers.")
            push_to_github()
        else:
            print("⏸️ Market closed — sleeping 10 min.")
            time.sleep(600)
        time.sleep(log_interval)

run_logger()
