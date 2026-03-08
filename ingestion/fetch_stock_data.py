from nsetools import Nse
import sqlite3
from datetime import datetime
import os

nse = Nse()

SYMBOLS = [
    "BANDHANBNK", "CGPOWER", "COALINDIA", "COCHINSHIP",
    "IDEA", "IRCON", "SUZLON", "TCS", "YESBANK"
]

os.makedirs("../database", exist_ok=True)
conn = sqlite3.connect("../database/stock_data.db")
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

for symbol in SYMBOLS:
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
