import streamlit as st
import pandas as pd
import concurrent.futures
import re
import yfinance as yf

st.set_page_config(page_title="AI Institutional Radar", layout="wide")
st.title("🛡️ AI Automatic Multibagger Radar (Ultra-Automation Mode)")
st.caption("Live Scanning 100+ Market Stocks for Volume Breakouts & News Velocity — Zero Input Required")

st.warning(
    "⚠️ **Disclaimer:** This is an educational screening tool, NOT financial advice. "
    "Please consult a SEBI-registered investment advisor before investing.",
    icon="⚠️"
)

# ----------------------------------------------------------------------------------
# 1. Automatic 100-Stock Universe (Small & Mid-Cap High Action Pool)
# ----------------------------------------------------------------------------------
AUTOMATED_UNIVERSE = [
    # Energy, Power & Green Tech
    "SUZLON.NS", "KPIGREEN.NS", "IREDA.NS", "INOXWIND.NS", "TATAPOWER.NS", "BORORENEW.NS", 
    "SWSOLAR.NS", "JSWENERGY.NS", "ORIANA.NS", "NHPC.NS", "SJVN.NS", "SWSOLAR.NS",
    # Defense, Aerospace & Engineering
    "DATAPATTERNS.NS", "KAYNES.NS", "BDL.NS", "MAZDOCK.NS", "HAL.NS", "BEL.NS", 
    "COCHINSHIP.NS", "AVANTEL.NS", "IDEAFORGE.NS", "ZENITH.NS", "BEML.NS", "MTAR.NS",
    # Railways & Infra Infrastructure
    "RVNL.NS", "IRFC.NS", "IRCON.NS", "RAILTEL.NS", "TEXRAIL.NS", "TITAGARH.NS", 
    "HBLPOWER.NS", "JWL.NS", "NCC.NS", "NBCC.NS", "PNCINFRA.NS", "HFCL.NS",
    # AI, Tech, EMS & Semiconductors
    "NETWEB.NS", "HITACHI.NS", "SYRMA.NS", "MOSCHIP.NS", "TEJASNET.NS", "ZENSARTECH.NS", 
    "KPIT.NS", "CYIENT.NS", "TATAELXSI.NS", "CEINFO.NS", "AFFLE.NS",
    # Chemicals, Commodities & Metals
    "DEEPAKNIT.NS", "NATCOPHARM.NS", "NEOGEN.NS", "TATACHEM.NS", "HINDCOPPER.NS", 
    "NATIONALUM.NS", "AETHER.NS", "ANUPAMRAS.NS", "TATAMETALI.NS",
    # High-Growth Mid/Small-Caps (Automotive & Manufacturing)
    "TVSMOTOR.NS", "VOLTAS.NS", "GEPIL.NS", "KIRLOSENG.NS", "AMARAJABAT.NS", "EXIDEIND.NS",
    "SONACOMS.NS", "BALAMINES.NS", "ALKALI.NS", "SUPREMEIND.NS", "POLYMED.NS",
    # Trending / Turnaround Candidates
    "RELIANCE.NS", "INFY.NS", "SBIN.NS", "GAIL.NS", "ITC.NS", "JIOFIN.NS"
]

# Formatting names nicely for UI
auto_universe = [t.strip().upper() for t in AUTOMATED_UNIVERSE]

scan_clicked = st.button("🚀 Start 100+ Stock Automated Scan Now", use_container_width=True)
st.caption(f"🤖 AI Radar is currently monitoring {len(auto_universe)} institutional small & mid-cap stocks.")

# ----------------------------------------------------------------------------------
# Sentiment & Catalyst Engine
# ----------------------------------------------------------------------------------
POSITIVE_TRIGGERS = {
    'order': 'Huge Order Win 💰',
    'expansion': 'Capacity Expansion 🏭',
    'capex': 'Capex Boost 📈',
    'profit': 'Surging Profits 🚀',
    'acquisition': 'Strategic Acquisition 🤝',
    'joint venture': 'JV Partnership 🤝'
}

NEGATIVE_CONTEXT_WORDS = [
    'cancel', 'cancelled', 'decline', 'declined', 'delay', 'delayed',
    'loss', 'losses', 'shrink', 'shrinks', 'fraud', 'scam', 'penalty', 'fine'
]

def evaluate_news(news_items):
    catalyst = "No Major Catalyst"
    sentiment_score = 0
    if not news_items or not isinstance(news_items, list):
        return catalyst, sentiment_score

    for item in news_items[:5]:
        title = item.get('title', '').lower()
        if any(neg in title for neg in NEGATIVE_CONTEXT_WORDS):
            sentiment_score -= 1
            continue
        for key, msg in POSITIVE_TRIGGERS.items():
            if re.search(rf"\b{key}\w*\b", title):
                catalyst = msg
                sentiment_score += 2
    return catalyst, sentiment_score

def normalize_debt_to_equity(raw_de):
    if raw_de is None: return 0.0
    try:
        raw_de = float(raw_de)
        return raw_de / 100 if raw_de > 10 else raw_de
    except ValueError: return 0.0

@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(ticker: str):
    stock = yf.Ticker(ticker)
    info = stock.info

    if not info or not isinstance(info, dict): raise ValueError("No Data")

    price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0
    if price == 0: raise ValueError("Price Error")

    mcap = (info.get('marketCap') or 0) / 10000000
    roe = (info.get('returnOnEquity') or 0) * 100
    debt_to_equity = normalize_debt_to_equity(info.get('debtToEquity', 0))
    revenue_growth = (info.get('revenueGrowth') or 0) * 100

    avg_volume = info.get('averageVolume') or 1
    current_volume = info.get('volume') or 1
    volume_shock = float(current_volume) / float(avg_volume) if avg_volume > 0 else 1.0

    try: news = stock.news
    except Exception: news = []
        
    catalyst, sentiment_score = evaluate_news(news)

    # Scoring Engine
    score = 0
    if roe > 12: score += 2
    if 0 <= debt_to_equity < 1.0: score += 2
    if revenue_growth > 15: score += 2
    if volume_shock > 1.5: score += 2
    score += max(sentiment_score, 0)
    if sentiment_score < 0: score -= 2

    if score >= 9:
        verdict = "🔥 STRONG BUY (Institutional Entry)"
    elif score >= 6:
        verdict = "⏳ ACCUMULATE (Watchlist)"
    elif debt_to_equity > 1.5 or sentiment_score < 0:
        verdict = "❌ AVOID (Risk Flag)"
    else:
        verdict = "👀 HOLD / WAIT"

    return {
        "Stock": ticker,
        "Price (₹)": round(float(price), 2),
        "Market Cap (Cr)": round(mcap, 2),
        "ROE (%)": round(roe, 2),
        "Debt/Equity": round(debt_to_equity, 2),
        "Growth (%)": round(revenue_growth, 2),
        "Volume Spike": f"{round(volume_shock, 1)}x",
        "Detected Catalyst": catalyst,
        "Score": score,
        "AI Action Verdict": verdict,
    }

def style_verdict(val):
    if "STRONG BUY" in val: return "background-color: #d4f7d4; color: #0a5d0a; font-weight: 600;"
    if "ACCUMULATE" in val: return "background-color: #fff6cc; color: #7a5c00; font-weight: 600;"
    if "AVOID" in val: return "background-color: #f8d4d4; color: #7a0a0a; font-weight: 600;"
    return "background-color: #eaeaea; color: #444;"

if scan_clicked:
    results = []
    failed = []
    progress_bar = st.progress(0, text="Initializing automated AI radar...")
    total = len(auto_universe)
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {executor.submit(fetch_stock_data, ticker): ticker for ticker in auto_universe}
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            completed += 1
            progress_bar.progress(completed / total, text=f"AI Scanning {completed}/{total} — {ticker}")
            try: results.append(future.result())
            except Exception as e: failed.append((ticker, str(e)))

    progress_bar.empty()

    if results:
        df = pd.DataFrame(results)
        st.subheader("📊 Top Auto-Discovered Opportunities (Highest Score First)")

        sort_rank = {"STRONG BUY": 0, "ACCUMULATE": 1, "HOLD": 2, "AVOID": 3}
        df['sort_order'] = df['AI Action Verdict'].apply(lambda x: next((v for k, v in sort_rank.items() if k in x), 4))
        df = df.sort_values(['sort_order', 'Score'], ascending=[True, False]).drop(columns=['sort_order'])

        styler = df.style
        if hasattr(styler, "map"): styled_df = styler.map(style_verdict, subset=['AI Action Verdict'])
        else: styled_df = styler.applymap(style_verdict, subset=['AI Action Verdict'])
        
        st.dataframe(styled_df, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Strong Buys 🔥", int(df['AI Action Verdict'].str.contains('STRONG BUY').sum()))
        c2.metric("Accumulate ⏳", int(df['AI Action Verdict'].str.contains('ACCUMULATE').sum()))
        c3.metric("Avoid ❌", int(df['AI Action Verdict'].str.contains('AVOID').sum()))

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Strategy Sheet 📥", data=csv, file_name="AI_Automated_Signals.csv", mime="text/csv")
        
