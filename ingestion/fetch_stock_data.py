from jugaad_data.nse import stock_df
import sqlite3
import os
from datetime import date, datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_data.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS stock_prices (
    symbol TEXT, datetime TEXT, open REAL,
    high REAL, low REAL, close REAL, fetched_at TEXT,
    PRIMARY KEY (symbol, datetime)
)
""")

c.execute("SELECT DISTINCT symbol FROM stock_prices")
symbols = [row[0] for row in c.fetchall()]

if not symbols:
    print("No stocks in DB yet.")
else:
    today = date.today()
    from_date = today - timedelta(days=3)

    for symbol in symbols:
        try:
            df = stock_df(symbol=symbol, from_date=from_date,
                          to_date=today, series="EQ")
            if df.empty:
                print(f"No data for {symbol}")
                continue

            for _, row in df.iterrows():
                c.execute("INSERT OR IGNORE INTO stock_prices VALUES (?,?,?,?,?,?,?)", (
                    symbol,
                    str(row["DATE"].date()),
                    float(row["OPEN"]),
                    float(row["HIGH"]),
                    float(row["LOW"]),
                    float(row["CLOSE"]),
                    datetime.now().isoformat()
                ))

            print(f"✓ {symbol} updated")

        except Exception as e:
            print(f"✗ {symbol} failed: {e}")

conn.commit()
conn.close()
print("Done.")
