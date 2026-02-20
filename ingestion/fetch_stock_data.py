from twelvedata import TDClient
import sqlite3
from datetime import datetime

SYMBOLS = ["TSLA", "AAPL", "MSFT", "GOOGL", "AMZN"]

td = TDClient(apikey="4d363c98b2d04b3fbff58a21ff4dbcad")

conn = sqlite3.connect("stock_data.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS stock_prices (
    symbol TEXT,
    datetime TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    fetched_at TEXT
)
""")

for symbol in SYMBOLS:
    ts = td.time_series(
        symbol=symbol,
        interval="1min",
        outputsize=5
    )

    data = ts.as_json()

    for row in data:
        c.execute("""
        INSERT INTO stock_prices
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            row["datetime"],
            float(row["open"]),
            float(row["high"]),
            float(row["low"]),
            float(row["close"]),
            int(row["volume"]),
            datetime.now().isoformat()
        ))

conn.commit()
conn.close()

print("Data inserted correctly.")