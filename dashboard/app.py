import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import yfinance as yf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_data.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

st.set_page_config(page_title="MoneyUp", layout="wide", page_icon="🪙")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #0d0d14; color: #e0e0e0; }
    .stApp { background-color: #0d0d14; }
    h1, h2, h3 { font-family: 'Space Mono', monospace; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 700; }
    div[data-testid="stMetricDelta"] { font-size: 14px; }
    .section-title { font-family: 'Space Mono', monospace; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; color: #555577; margin-bottom: 16px; }
    .stTabs [data-baseweb="tab"] { font-family: 'Space Mono', monospace; font-size: 12px; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

st.title("🪙 MoneyUp — NSE Stock Analysis Dashboard")
st.info(f"📅 Data as of {(datetime.now() - timedelta(days=1)).strftime('%d %b %Y')} · Prices are previous trading day's closing prices")
st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)

# ── Helper ─────────────────────────────────────────────────
def ensure_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS stock_prices (
        symbol TEXT, datetime TEXT, open REAL,
        high REAL, low REAL, close REAL, fetched_at TEXT,
        PRIMARY KEY (symbol, datetime)
    )
    """)
    conn.commit()
    conn.close()

ensure_table()

# ── Sidebar ────────────────────────────────────────────────
st.sidebar.title("🪙 MoneyUp")
st.sidebar.markdown("---")

# ADD STOCK
st.sidebar.markdown("**➕ Add a Stock**")
new_symbol = st.sidebar.text_input("NSE Symbol (e.g. TCS, HDFCBANK)", "").upper().strip()

if st.sidebar.button("Add Stock"):
    if new_symbol:
        with st.spinner(f"Loading data for {new_symbol}..."):
            try:
                ticker = yf.Ticker(f"{new_symbol}.NS")
                data = ticker.history(start="2026-01-01", end=datetime.today().strftime("%Y-%m-%d"), interval="1d")

                if data.empty:
                    st.sidebar.error(f"✗ '{new_symbol}' not found. Check the NSE symbol and try again.")
                else:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("DELETE FROM stock_prices WHERE symbol = ?", (new_symbol,))
                    for dt, row in data.iterrows():
                        c.execute("INSERT OR IGNORE INTO stock_prices VALUES (?,?,?,?,?,?,?)", (
                            new_symbol,
                            str(dt.date()),
                            float(row["Open"]),
                            float(row["High"]),
                            float(row["Low"]),
                            float(row["Close"]),
                            datetime.now().isoformat()
                        ))
                    conn.commit()
                    conn.close()
                    st.sidebar.success(f"✓ {new_symbol} added with {len(data)} days of data!")
                    st.cache_data.clear()
                    st.rerun()
            except Exception as e:
                st.sidebar.error(f"✗ Error: {e}")

# REMOVE STOCK
st.sidebar.markdown("---")
st.sidebar.markdown("**➖ Remove a Stock**")

conn_s = sqlite3.connect(DB_PATH)
existing_symbols = pd.read_sql_query("SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol", conn_s)["symbol"].tolist()
conn_s.close()

if existing_symbols:
    remove_symbol = st.sidebar.selectbox("Select stock to remove", existing_symbols)
    if st.sidebar.button("Remove Stock"):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM stock_prices WHERE symbol = ?", (remove_symbol,))
        conn.commit()
        conn.close()
        st.sidebar.success(f"✓ {remove_symbol} removed!")
        st.cache_data.clear()
        st.rerun()

# ── Load Data ──────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM stock_prices", conn)
    conn.close()
    df["datetime"] = pd.to_datetime(df["datetime"], format="mixed")
    df = df.sort_values("datetime")
    return df

df = load_data()

if df.empty:
    st.info("👈 No stocks yet. Add a stock from the sidebar to get started.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs([
    "🏠  OVERVIEW", "🔍  DEEP DIVE", "📊  ANALYSIS", "⚖️  COMPARE"
])

# ══════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-title">All Stocks — Latest Snapshot</p>', unsafe_allow_html=True)

    latest_df = df.groupby("symbol").last().reset_index()
    first_df  = df.groupby("symbol").first().reset_index()
    merged = latest_df[["symbol","close"]].merge(
        first_df[["symbol","close"]], on="symbol", suffixes=("_latest","_first")
    )
    merged["change"]     = merged["close_latest"] - merged["close_first"]
    merged["pct_change"] = (merged["change"] / merged["close_first"]) * 100

    symbols = sorted(merged["symbol"].tolist())
    cols = st.columns(3)
    for i, sym in enumerate(symbols):
        row = merged[merged["symbol"] == sym].iloc[0]
        cols[i % 3].metric(
            label=sym,
            value=f"₹{row['close_latest']:,.2f}",
            delta=f"{row['change']:+.2f} ({row['pct_change']:+.2f}%)",
            delta_color="normal"
        )

    st.divider()
    st.markdown('<p class="section-title">% Price Change — All Stocks Over Time</p>', unsafe_allow_html=True)
    overview_range = st.radio("Range", ["7 Days", "30 Days", "All Time"], horizontal=True)

    now = df["datetime"].max()
    if overview_range == "7 Days":
        ov_start = now - timedelta(days=7)
    elif overview_range == "30 Days":
        ov_start = now - timedelta(days=30)
    else:
        ov_start = df["datetime"].min()

    fig_overview = go.Figure()
    colors = px.colors.qualitative.Safe
    for i, sym in enumerate(symbols):
        sym_df = df[(df["symbol"] == sym) & (df["datetime"] >= ov_start)].copy().reset_index(drop=True)
        if sym_df.empty or sym_df["close"].iloc[0] == 0:
            continue
        base = sym_df["close"].iloc[0]
        sym_df["pct"] = ((sym_df["close"] - base) / base) * 100
        fig_overview.add_trace(go.Scatter(
            x=sym_df["datetime"], y=sym_df["pct"],
            name=sym, mode="lines",
            line=dict(width=2, color=colors[i % len(colors)])
        ))

    fig_overview.add_hline(y=0, line_dash="dash", line_color="#333355")
    fig_overview.update_layout(
        paper_bgcolor="#111120", plot_bgcolor="#111120",
        font=dict(color="#aaaacc"),
        yaxis_title="% Change from Start",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(showgrid=False, rangebreaks=[dict(bounds=["sat","mon"])]),
        yaxis=dict(showgrid=True, gridcolor="#1e1e35"),
        height=420, margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_overview, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 2 — DEEP DIVE
# ══════════════════════════════════════════════════════════
with tab2:
    col_left, col_right = st.columns([1, 3])
    with col_left:
        selected_symbol = st.selectbox("Select Stock", sorted(df["symbol"].unique()), key="dd_symbol")
        time_range = st.radio("Time Range", ["Last 7 Days", "Last 30 Days", "All Time"], key="dd_range")

    now = df["datetime"].max()
    if time_range == "Last 7 Days":
        start = now - timedelta(days=7)
    elif time_range == "Last 30 Days":
        start = now - timedelta(days=30)
    else:
        start = df["datetime"].min()

    filtered = df[(df["symbol"] == selected_symbol) & (df["datetime"] >= start)].copy()

    if filtered.empty:
        st.warning("No data for this range yet.")
    else:
        latest  = filtered.iloc[-1]
        first   = filtered.iloc[0]
        p_change = latest["close"] - first["close"]
        pct      = (p_change / first["close"]) * 100

        with col_right:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Current Price",    f"₹{latest['close']:,.2f}", f"{p_change:+.2f} ({pct:+.2f}%)")
            m2.metric("Highest Price",    f"₹{filtered['high'].max():,.2f}")
            m3.metric("Lowest Price",     f"₹{filtered['low'].min():,.2f}")
            m4.metric("Price Swing",      f"₹{filtered['high'].max() - filtered['low'].min():,.2f}")

        fig2 = go.Figure(go.Candlestick(
            x=filtered["datetime"],
            open=filtered["open"], high=filtered["high"],
            low=filtered["low"],   close=filtered["close"],
            increasing_line_color="#00e676", decreasing_line_color="#ff1744"
        ))
        fig2.update_layout(
            paper_bgcolor="#111120", plot_bgcolor="#111120",
            font=dict(color="#aaaacc"),
            xaxis_rangeslider_visible=False,
            xaxis=dict(showgrid=False, rangebreaks=[dict(bounds=["sat","mon"])]),
            yaxis=dict(showgrid=True, gridcolor="#1e1e35", title="Price (₹)"),
            height=500, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Clean price history table
        st.markdown('<p class="section-title">Price History</p>', unsafe_allow_html=True)
        display_df = filtered[["datetime","open","high","low","close"]].copy()
        display_df["datetime"] = display_df["datetime"].dt.strftime("%d %b %Y")
        display_df = display_df.drop_duplicates(subset=["datetime"])
        display_df.columns = ["Date", "Open ₹", "High ₹", "Low ₹", "Close ₹"]
        display_df = display_df.sort_values("Date", ascending=False).head(20).reset_index(drop=True)
        display_df.index = display_df.index + 1
        st.dataframe(display_df, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 3 — ANALYSIS
# ══════════════════════════════════════════════════════════
with tab3:
    conn = sqlite3.connect(DB_PATH)

    st.markdown('<p class="section-title">Average Closing Price Per Stock</p>', unsafe_allow_html=True)
    avg_df = pd.read_sql_query("SELECT symbol, ROUND(AVG(close),2) AS avg_price FROM stock_prices GROUP BY symbol ORDER BY avg_price DESC", conn)
    fig_avg = px.bar(avg_df, x="symbol", y="avg_price", color="avg_price", color_continuous_scale="Blues", text="avg_price")
    fig_avg.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig_avg.update_layout(paper_bgcolor="#111120", plot_bgcolor="#111120", font=dict(color="#aaaacc"),
                          showlegend=False, xaxis=dict(showgrid=False, title="Stock"),
                          yaxis=dict(showgrid=True, gridcolor="#1e1e35", title="Average Price (₹)"),
                          margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_avg, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<p class="section-title">Price Swing — Highest to Lowest</p>', unsafe_allow_html=True)
        vol_df = pd.read_sql_query("SELECT symbol, ROUND(MAX(high)-MIN(low),2) AS volatility FROM stock_prices GROUP BY symbol ORDER BY volatility DESC", conn)
        fig_vol = px.bar(vol_df, x="symbol", y="volatility", color="volatility", color_continuous_scale="Reds", text="volatility")
        fig_vol.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig_vol.update_layout(paper_bgcolor="#111120", plot_bgcolor="#111120", font=dict(color="#aaaacc"),
                              showlegend=False, xaxis=dict(showgrid=False, title="Stock"),
                              yaxis=dict(showgrid=True, gridcolor="#1e1e35", title="Price Swing (₹)"),
                              margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_vol, use_container_width=True)

    with col_b:
        st.markdown('<p class="section-title">Highest vs Lowest Price Recorded</p>', unsafe_allow_html=True)
        hl_df = pd.read_sql_query("SELECT symbol, MAX(high) AS highest, MIN(low) AS lowest FROM stock_prices GROUP BY symbol ORDER BY highest DESC", conn)
        fig_hl = go.Figure()
        fig_hl.add_trace(go.Bar(name="Highest", x=hl_df["symbol"], y=hl_df["highest"], marker_color="#00e676"))
        fig_hl.add_trace(go.Bar(name="Lowest",  x=hl_df["symbol"], y=hl_df["lowest"],  marker_color="#ff1744"))
        fig_hl.update_layout(barmode="group", paper_bgcolor="#111120", plot_bgcolor="#111120",
                             font=dict(color="#aaaacc"), legend=dict(orientation="h"),
                             xaxis=dict(showgrid=False, title="Stock"),
                             yaxis=dict(showgrid=True, gridcolor="#1e1e35", title="Price (₹)"),
                             margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_hl, use_container_width=True)

    st.markdown('<p class="section-title">Percentage Change — January 1 to Today</p>', unsafe_allow_html=True)
    change_df = pd.read_sql_query("""
        SELECT f.symbol,
            ROUND(f.close,2) AS "Price on Jan 1 (₹)",
            ROUND(l.close,2) AS "Latest Price (₹)",
            ROUND(l.close-f.close,2) AS "Change (₹)",
            ROUND((l.close-f.close)/f.close*100,2) AS "Percentage Change (%)"
        FROM
            (SELECT symbol, close FROM stock_prices WHERE datetime=(SELECT MIN(datetime) FROM stock_prices s2 WHERE s2.symbol=stock_prices.symbol)) f
        JOIN
            (SELECT symbol, close FROM stock_prices WHERE datetime=(SELECT MAX(datetime) FROM stock_prices s2 WHERE s2.symbol=stock_prices.symbol)) l
        ON f.symbol=l.symbol ORDER BY "Percentage Change (%)" DESC
    """, conn)

    if not change_df.empty:
        fig_change = px.bar(change_df, x="symbol", y="Percentage Change (%)",
                            color="Percentage Change (%)", text="Percentage Change (%)",
                            color_continuous_scale=["#ff1744","#1a1a2e","#00e676"],
                            color_continuous_midpoint=0)
        fig_change.update_traces(texttemplate="%{text:+.2f}%", textposition="outside")
        fig_change.update_layout(paper_bgcolor="#111120", plot_bgcolor="#111120", font=dict(color="#aaaacc"),
                                 showlegend=False, xaxis=dict(showgrid=False, title="Stock"),
                                 yaxis=dict(showgrid=True, gridcolor="#1e1e35"),
                                 margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_change, use_container_width=True)
        st.dataframe(change_df.reset_index(drop=True), use_container_width=True)

    conn.close()

# ══════════════════════════════════════════════════════════
# TAB 4 — COMPARE
# ══════════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-title">Compare Stocks — Percentage Change from Start</p>', unsafe_allow_html=True)
    selected_stocks = st.multiselect(
        "Pick stocks to compare",
        sorted(df["symbol"].unique()),
        default=sorted(df["symbol"].unique())[:min(3, len(df["symbol"].unique()))],
        key="cmp_stocks"
    )

    if len(selected_stocks) < 2:
        st.info("Select at least 2 stocks to compare.")
    else:
        fig_cmp = go.Figure()
        colors = px.colors.qualitative.Safe
        for i, sym in enumerate(selected_stocks):
            sym_df = df[df["symbol"] == sym].copy().reset_index(drop=True)
            if sym_df.empty or sym_df["close"].iloc[0] == 0:
                continue
            base = sym_df["close"].iloc[0]
            sym_df["normalized"] = ((sym_df["close"] - base) / base) * 100
            fig_cmp.add_trace(go.Scatter(
                x=sym_df["datetime"], y=sym_df["normalized"],
                name=sym, mode="lines",
                line=dict(width=2, color=colors[i % len(colors)])
            ))

        fig_cmp.add_hline(y=0, line_dash="dash", line_color="#333355")
        fig_cmp.update_layout(
            paper_bgcolor="#111120", plot_bgcolor="#111120",
            font=dict(color="#aaaacc"),
            yaxis_title="Percentage Change (%)",
            xaxis=dict(showgrid=False, rangebreaks=[dict(bounds=["sat","mon"])]),
            yaxis=dict(showgrid=True, gridcolor="#1e1e35"),
            height=450, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        stats = []
        for sym in selected_stocks:
            sym_df = df[df["symbol"] == sym]
            if sym_df.empty:
                continue
            latest_p = sym_df["close"].iloc[-1]
            first_p  = sym_df["close"].iloc[0]
            stats.append({
                "Stock": sym,
                "Current Price": f"₹{latest_p:,.2f}",
                "Highest Price": f"₹{sym_df['high'].max():,.2f}",
                "Lowest Price": f"₹{sym_df['low'].min():,.2f}",
                "Average Price": f"₹{sym_df['close'].mean():,.2f}",
                "Price Swing": f"₹{sym_df['high'].max()-sym_df['low'].min():,.2f}",
                "Percentage Change": f"{((latest_p-first_p)/first_p)*100:+.2f}%",
                "Days of Data": len(sym_df)
            })
        st.dataframe(pd.DataFrame(stats).set_index("Stock"), use_container_width=True)