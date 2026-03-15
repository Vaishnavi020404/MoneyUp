# 💹 MoneyUp — Live NSE Stock Analysis Dashboard

A real-time NSE stock analysis dashboard that automatically fetches, stores, and visualizes Indian stock market data. Built as a complete data engineering project — from automated data ingestion to deployed interactive dashboard.

**Live App:** [moneyup.streamlit.app](https://moneyup.streamlit.app)

---

##  What Makes This Different

Most data projects analyze static Kaggle datasets. MoneyUp is **live and automated** — it fetches real NSE closing prices every weekday without any manual intervention, and anyone can open the link and see up-to-date stock analysis instantly. No login required — open the link and start analyzing.

---

## Features

**Overview** — Latest prices and percentage change for all tracked stocks since January 1, 2026. **Deep Dive** — Candlestick charts with OHLC data, price metrics, and full price history for any stock. **Analysis** — Average price, volatility, highest vs lowest price, and percentage change charts powered by SQL queries. **Compare** — Normalized percentage change comparison across multiple stocks on the same chart. **Add / Remove Stocks** — Dynamically add any NSE listed stock from the sidebar — loads 45+ days of historical data instantly. **Auto Refresh** — Dashboard refreshes every 60 seconds.

---

##  How It Works

NSE Official Data → Python Ingestion Script → SQLite Database → Streamlit Dashboard. GitHub Actions runs the ingestion script automatically every weekday at 5:30 PM IST, commits the updated database back to the repo, and Streamlit Cloud serves the latest data to anyone who opens the link.

1. Data is fetched from NSE directly using the jugaad-data library — official NSE closing prices, no approximations
2. Stored in a SQLite database inside the GitHub repository
3. GitHub Actions workflow triggers automatically every weekday — zero manual effort
4. Streamlit dashboard reads from the database and renders interactive Plotly charts
5. Deployed on Streamlit Cloud — publicly accessible to anyone

---

##  Project Structure

.github/workflows/fetch_stocks.yml — GitHub Actions automation pipeline. ingestion/fetch_stock_data.py — Daily fetch script triggered by GitHub Actions. ingestion/load_historical.py — One-time script to load historical data from Jan 1 2026. ingestion/cleanup.py — Database cleanup utility. dashboard/app.py — Full Streamlit dashboard with all 4 tabs. database/stock_data.db — SQLite database. analysis/stock_analysis.sql — SQL queries used in the analysis tab. requirements.txt — Python dependencies.

---

##  Tech Stack

Python — data ingestion, analysis, dashboard. jugaad-data — official NSE stock data. SQLite — lightweight database. Pandas — data manipulation. SQL — analytical queries. Plotly — interactive charts. Streamlit — dashboard framework and deployment. GitHub Actions — automated CI/CD pipeline.

---

##  Analysis Performed

Average closing price per stock since January 1. Highest and lowest price recorded per stock. Price volatility calculated as max high minus min low. Percentage change from first recorded date to latest. Normalized cross-stock comparison showing relative performance. Candlestick OHLC chart per stock with configurable time ranges.

---

## Run Locally

Clone the repo, install dependencies with pip install -r requirements.txt, run python ingestion/load_historical.py to load historical data, then run python -m streamlit run dashboard/app.py to start the dashboard.

---

## About

Built by Vaishnavi Pandey as a data analytics portfolio project. Open to Data Analyst and Data Science internship opportunities in Mumbai.

🔗 LinkedIn: https://www.linkedin.com/in/vaishnavi-pandey-0106a6283/ |  GitHub: https://github.com/Vaishnavi020404/
