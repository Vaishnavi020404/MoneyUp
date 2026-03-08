import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="NSE Stock Dashboard", layout="wide", page_icon="📈")

# Auto-refresh every 60 seconds
st_autorefresh = st.empty()
count = st_autorefresh.text("")
time_holder = st.sidebar.empty()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #0d0d14; color: #e0e0e0; }
    .stApp { background-color: #0d0d14; }
    h1, h2, h3 { font-family: 'Space Mono', monospace; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 700; }
    div[data-testid="stMetricDelta"] { font-size: 14px; }
    .section-title { font-family: 'Space Mono', monospace; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; color: #555577; margin-bottom: 16px; }
    div[data-testid="stHorizontalBlock"] > div { background: #111120; border: 1px solid #1e1e35; border-radius: 10px; padding: 8px; }
    .stTabs [data-baseweb="tab"] { font-family: 'Space Mono', monospace; font-size: 12px; letter-spacing: 1px; }
    .stDataFrame { background: #111120; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ──────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect("../database/stock_data.db")
    df = pd.read_sql_query("SELECT * FROM stock_prices", conn)
    conn.close()
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")
    return df

df = load_data()

st.title("📈 NSE Stock Market Dashboard")
st.caption(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')} · Auto-refreshes every 60s")

# Auto refresh
st.markdown("""
<script>
    setTimeout(function(){ window.location.reload(); }, 60000);
</script>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠  OVERVIEW",
    "🔍  DEEP DIVE",
    "📊  ANALYSIS",
    "⚖️  COMPARE"
])

# ══════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-title">All Stocks — Latest Snapshot</p>', unsafe_allow_html=True)

    # Latest price per stock
    latest_df = df.sort_values("datetime").groupby("symbol").last().reset_index()
    first_df  = df.sort_values("datetime").groupby("symbol").first().reset_index()

    latest_df["change"]     = latest_df["close"] - first_df["close"]
    latest_df["pct_change"] = (latest_df["change"] / first_df["close"]) * 100

    # Metric cards — 3 per row
    symbols = sorted(latest_df["symbol"].tolist())
    cols = st.columns(3)
    for i, sym in enumerate(symbols):
        row = latest_df[latest_df["symbol"] == sym].iloc[0]
        delta = f"{row['change']:+.2f} ({row['pct_change']:+.2f}%)"
        cols[i % 3].metric(
            label=sym,
            value=f"₹{row['close']:,.2f}",
            delta=delta,
            delta_color="normal"
        )

    st.divider()
    st.markdown('<p class="section-title">Price Movement — All Stocks</p>', unsafe_allow_html=True)

    # Mini sparkline for each stock in one chart
    fig_overview = go.Figure()
    colors = px.colors.qualitative.Safe
    for i, sym in enumerate(symbols):
        sym_df = df[df["symbol"] == sym]
        fig_overview.add_trace(go.Scatter(
            x=sym_df["datetime"],
            y=sym_df["close"],
            name=sym,
            mode="lines",
            line=dict(width=1.5, color=colors[i % len(colors)])
        ))

    fig_overview.update_layout(
        paper_bgcolor="#111120", plot_bgcolor="#111120",
        font=dict(color="#aaaacc"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#1e1e35"),
        height=400, margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig_overview, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 2 — DEEP DIVE
# ══════════════════════════════════════════════════════════
with tab2:
    col_left, col_right = st.columns([1, 3])

    with col_left:
        selected_symbol = st.selectbox("Select Stock", sorted(df["symbol"].unique()))
        time_range = st.radio("Time Range", ["Last Hour", "Today", "Last 7 Days", "All Time"])

    now = df["datetime"].max()
    if time_range == "Last Hour":
        start = now - timedelta(hours=1)
    elif time_range == "Today":
        start = now - timedelta(days=1)
    elif time_range == "Last 7 Days":
        start = now - timedelta(days=7)
    else:
        start = df["datetime"].min()

    filtered = df[(df["symbol"] == selected_symbol) & (df["datetime"] >= start)].copy()

    if filtered.empty:
        st.warning("No data for this range yet. Keep your automation script running.")
    else:
        latest  = filtered.iloc[-1]
        first   = filtered.iloc[0]
        p_change = latest["close"] - first["close"]
        pct      = (p_change / first["close"]) * 100

        with col_right:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Price",    f"₹{latest['close']:,.2f}", f"{p_change:+.2f} ({pct:+.2f}%)")
            m2.metric("High",     f"₹{filtered['high'].max():,.2f}")
            m3.metric("Low",      f"₹{filtered['low'].min():,.2f}")
            m4.metric("Volatility", f"₹{filtered['high'].max() - filtered['low'].min():,.2f}")

        # Candlestick + Volume
        fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                             row_heights=[0.75, 0.25], vertical_spacing=0.03)

        fig2.add_trace(go.Candlestick(
            x=filtered["datetime"],
            open=filtered["open"], high=filtered["high"],
            low=filtered["low"],   close=filtered["close"],
            name="OHLC",
            increasing_line_color="#00e676",
            decreasing_line_color="#ff1744"
        ), row=1, col=1)

        bar_colors = ["#00e676" if c >= o else "#ff1744"
                      for c, o in zip(filtered["close"], filtered["open"])]

        fig2.add_trace(go.Bar(
            x=filtered["datetime"],
            y=[1] * len(filtered),  # placeholder if no volume
            name="Fetches",
            marker_color=bar_colors,
            opacity=0.5
        ), row=2, col=1)

        fig2.update_layout(
            paper_bgcolor="#111120", plot_bgcolor="#111120",
            font=dict(color="#aaaacc"),
            xaxis_rangeslider_visible=False,
            xaxis2=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#1e1e35"),
            yaxis2=dict(showgrid=False),
            height=500, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h")
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<p class="section-title">Raw Data Table</p>', unsafe_allow_html=True)
        st.dataframe(
            filtered[["datetime", "open", "high", "low", "close"]].tail(20).sort_values("datetime", ascending=False),
            use_container_width=True
        )

# ══════════════════════════════════════════════════════════
# TAB 3 — SQL ANALYSIS
# ══════════════════════════════════════════════════════════
with tab3:
    conn = sqlite3.connect("../database/stock_data.db")

    st.markdown('<p class="section-title">Average Price Per Stock</p>', unsafe_allow_html=True)
    avg_df = pd.read_sql_query("""
        SELECT symbol, ROUND(AVG(close),2) AS avg_price
        FROM stock_prices GROUP BY symbol ORDER BY avg_price DESC
    """, conn)
    fig_avg = px.bar(avg_df, x="symbol", y="avg_price", color="avg_price",
                     color_continuous_scale="Blues", text="avg_price")
    fig_avg.update_layout(paper_bgcolor="#111120", plot_bgcolor="#111120",
                          font=dict(color="#aaaacc"), showlegend=False,
                          margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_avg, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<p class="section-title">Volatility (Price Range)</p>', unsafe_allow_html=True)
        vol_df = pd.read_sql_query("""
            SELECT symbol, ROUND(MAX(high)-MIN(low),2) AS volatility
            FROM stock_prices GROUP BY symbol ORDER BY volatility DESC
        """, conn)
        fig_vol = px.bar(vol_df, x="symbol", y="volatility", color="volatility",
                         color_continuous_scale="Reds", text="volatility")
        fig_vol.update_layout(paper_bgcolor="#111120", plot_bgcolor="#111120",
                              font=dict(color="#aaaacc"), showlegend=False,
                              margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_vol, use_container_width=True)

    with col_b:
        st.markdown('<p class="section-title">Records Collected Per Stock</p>', unsafe_allow_html=True)
        rec_df = pd.read_sql_query("""
            SELECT symbol, COUNT(*) AS records
            FROM stock_prices GROUP BY symbol ORDER BY records DESC
        """, conn)
        fig_rec = px.pie(rec_df, names="symbol", values="records",
                         color_discrete_sequence=px.colors.qualitative.Safe)
        fig_rec.update_layout(paper_bgcolor="#111120", plot_bgcolor="#111120",
                              font=dict(color="#aaaacc"), margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_rec, use_container_width=True)

    st.markdown('<p class="section-title">Price Change (First vs Latest)</p>', unsafe_allow_html=True)
    change_df = pd.read_sql_query("""
        SELECT 
            a.symbol,
            ROUND(a.close, 2) AS first_price,
            ROUND(b.close, 2) AS latest_price,
            ROUND(b.close - a.close, 2) AS change,
            ROUND((b.close - a.close) / a.close * 100, 2) AS pct_change
        FROM
            (SELECT symbol, close FROM stock_prices WHERE datetime IN (SELECT MIN(datetime) FROM stock_prices GROUP BY symbol)) a
        JOIN
            (SELECT symbol, close FROM stock_prices WHERE datetime IN (SELECT MAX(datetime) FROM stock_prices GROUP BY symbol)) b
        ON a.symbol = b.symbol
        ORDER BY pct_change DESC
    """, conn)
    fig_change = px.bar(change_df, x="symbol", y="pct_change",
                        color="pct_change", text="pct_change",
                        color_continuous_scale=["#ff1744", "#111120", "#00e676"],
                        color_continuous_midpoint=0)
    fig_change.update_layout(paper_bgcolor="#111120", plot_bgcolor="#111120",
                             font=dict(color="#aaaacc"), showlegend=False,
                             margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_change, use_container_width=True)

    conn.close()

# ══════════════════════════════════════════════════════════
# TAB 4 — COMPARE
# ══════════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-title">Compare Stocks Side by Side</p>', unsafe_allow_html=True)

    selected_stocks = st.multiselect("Pick stocks to compare", sorted(df["symbol"].unique()),
                                     default=sorted(df["symbol"].unique())[:3])

    if len(selected_stocks) < 2:
        st.info("Select at least 2 stocks to compare.")
    else:
        # Normalize to % change from first data point
        fig_cmp = go.Figure()
        colors = px.colors.qualitative.Safe
        for i, sym in enumerate(selected_stocks):
            sym_df = df[df["symbol"] == sym].copy()
            base = sym_df["close"].iloc[0]
            sym_df["normalized"] = ((sym_df["close"] - base) / base) * 100
            fig_cmp.add_trace(go.Scatter(
                x=sym_df["datetime"],
                y=sym_df["normalized"],
                name=sym,
                mode="lines",
                line=dict(width=2, color=colors[i % len(colors)])
            ))

        fig_cmp.add_hline(y=0, line_dash="dash", line_color="#333355")
        fig_cmp.update_layout(
            paper_bgcolor="#111120", plot_bgcolor="#111120",
            font=dict(color="#aaaacc"),
            yaxis_title="% Change from Start",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#1e1e35"),
            height=450, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        # Side by side stats table
        st.markdown('<p class="section-title">Stats Comparison</p>', unsafe_allow_html=True)
        stats = []
        for sym in selected_stocks:
            sym_df = df[df["symbol"] == sym]
            latest_p = sym_df["close"].iloc[-1]
            first_p  = sym_df["close"].iloc[0]
            stats.append({
                "Stock": sym,
                "Current ₹": f"₹{latest_p:,.2f}",
                "High ₹": f"₹{sym_df['high'].max():,.2f}",
                "Low ₹": f"₹{sym_df['low'].min():,.2f}",
                "Avg ₹": f"₹{sym_df['close'].mean():,.2f}",
                "Volatility": f"₹{sym_df['high'].max() - sym_df['low'].min():,.2f}",
                "% Change": f"{((latest_p - first_p)/first_p)*100:+.2f}%",
                "Data Points": len(sym_df)
            })
        st.dataframe(pd.DataFrame(stats).set_index("Stock"), use_container_width=True)