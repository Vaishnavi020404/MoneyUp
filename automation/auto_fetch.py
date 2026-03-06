import time
import subprocess

while True:
    print("Fetching sotck data...")
    subprocess.run(["python","fetch_stock_data.py"]
                   )
    print("Waiting 5 minutes")
    time.sleep(300)

    
