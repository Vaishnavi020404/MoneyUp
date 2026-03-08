import time
import subprocess

while True:
    print("Fetching stock data...")
    subprocess.run(["python","../ingestion/fetch_stock_data.py"]
                   )
    print("Waiting 1 minutes")
    time.sleep(60)

    
