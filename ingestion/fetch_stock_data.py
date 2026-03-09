from nsetools import Nse
import sqlite3
from datetime import datetime
import os

nse = Nse()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_data.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS stock_prices (
    symbol TEXT,
    datetime TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    fetched_at TEXT,
    PRIMARY KEY (symbol, fetched_at)
)
""")

# Read symbols from DB — whatever user has added
c.execute("SELECT DISTINCT symbol FROM stock_prices")
symbols = [row[0] for row in c.fetchall()]

if not symbols:
    print("No stocks in DB yet. User needs to add stocks from the dashboard first.")
else:
    for symbol in symbols:
        try:
            q = nse.get_quote(symbol)
            c.execute("""
            INSERT OR IGNORE INTO stock_prices VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                datetime.now().isoformat(),
                float(q["open"]),
                float(q["intraDayHighLow"]["max"]),
                float(q["intraDayHighLow"]["min"]),
                float(q["lastPrice"]),
                datetime.now().isoformat()
            ))
            print(f"✓ {symbol} — ₹{q['lastPrice']}")
        except Exception as e:
            print(f"✗ {symbol} failed: {e}")

conn.commit()
conn.close()