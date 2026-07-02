import streamlit as st
import pandas as pd
import concurrent.futures
import re

st.set_page_config(page_title="AI Institutional Radar", layout="wide")
st.title("🛡️ AI Automatic Multibagger Radar")
st.caption("Scanning Small & Mid-caps for Volume Breakouts & News Velocity")

st.warning(
    "⚠️ **Disclaimer:** This is an educational/informational screening tool, NOT financial advice. "
    "Verdicts are based on simple rule-based heuristics, not a trained ML model. "
    "Please consult a SEBI-registered investment advisor before making any investment decisions.",
    icon="⚠️"
)

# ----------------------------------------------------------------------------------
# 1. Universe selection — user can now edit/extend instead of it being fully hardcoded
# ----------------------------------------------------------------------------------
DEFAULT_UNIVERSE = [
    "SUZLON.NS", "KPIGREEN.NS", "IREDA.NS", "KAYNES.NS", "DATAPATTERNS.NS",
    "HBLPOWER.NS", "INOXWIND.NS", "NETWEB.NS", "HITACHI.NS", "RVNL.NS",
    "IRFC.NS", "NATCOPHARM.NS", "DEEPAKNIT.NS", "BDL.NS", "MAZDOCK.NS"
]

with st.expander("⚙️ Customize scan universe", expanded=False):
    custom_input = st.text_area(
        "Edit comma-separated NSE tickers (must end with .NS)",
        value=", ".join(DEFAULT_UNIVERSE),
        height=80
    )
    auto_universe = [t.strip().upper() for t in custom_input.split(",") if t.strip()]

col1, col2 = st.columns([1, 3])
with col1:
    scan_clicked = st.button("Start Automatic Market Scan ⚡", use_container_width=True)
with col2:
    st.caption(f"{len(auto_universe)} stocks in current scan universe")

# ----------------------------------------------------------------------------------
# Sentiment / catalyst detection — now checks for negation/negative context words
# so "order cancelled" doesn't get scored the same as "huge order win"
# ----------------------------------------------------------------------------------
POSITIVE_TRIGGERS = {
    'order': 'Huge Order Win 💰',
    'expansion': 'Capacity Expansion 🏭',
    'capex': 'Capex Boost 📈',
    'profit': 'Surging Profits 🚀',
    'acquisition': 'Strategic Acquisition 🤝',
}

NEGATIVE_CONTEXT_WORDS = [
    'cancel', 'cancelled', 'decline', 'declined', 'delay', 'delayed',
    'loss', 'losses', 'shrink', 'shrinks', 'shrinking', 'drop', 'dropped',
    'fall', 'falls', 'falling', 'probe', 'fraud', 'scam', 'downgrade',
    'default', 'lawsuit', 'penalty', 'fine', 'resign', 'resignation'
]

def evaluate_news(news_items):
    """Return (catalyst_label, sentiment_score) after checking for negative context."""
    catalyst = "No Major Catalyst"
    sentiment_score = 0
    if not news_items:
        return catalyst, sentiment_score

    for item in news_items[:5]:
        title = item.get('title', '').lower()
        # skip headline entirely if it contains negative-context words
        if any(neg in title for neg in NEGATIVE_CONTEXT_WORDS):
            sentiment_score -= 1
            continue
        for key, msg in POSITIVE_TRIGGERS.items():
            # word-boundary match to avoid partial-word false positives
            if re.search(rf"\b{key}\w*\b", title):
                catalyst = msg
                sentiment_score += 2
    return catalyst, sentiment_score


def normalize_debt_to_equity(raw_de):
    """yfinance sometimes returns D/E as a ratio (0.8) and sometimes as a
    percentage-like number (80). Normalize to a true ratio."""
    if raw_de is None:
        return 0.0
    raw_de = float(raw_de)
    return raw_de / 100 if raw_de > 10 else raw_de


@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(ticker: str):
    """Fetch and score a single stock. Cached for 5 minutes to avoid
    re-hitting the API on every click/rerun."""
    import yfinance as yf

    stock = yf.Ticker(ticker)
    info = stock.info

    price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0
    if not info or price == 0:
        raise ValueError("No market data returned (possibly delisted, wrong ticker, or rate-limited)")
    mcap = (info.get('marketCap', 0) or 0) / 10000000
    roe = (info.get('returnOnEquity', 0) or 0) * 100
    debt_to_equity = normalize_debt_to_equity(info.get('debtToEquity', 0))
    revenue_growth = (info.get('revenueGrowth', 0) or 0) * 100

    avg_volume = info.get('averageVolume', 1) or 1
    current_volume = info.get('volume', 1) or 1
    volume_shock = current_volume / avg_volume if avg_volume > 0 else 1

    news = stock.news
    catalyst, sentiment_score = evaluate_news(news)

    # ---- Weighted scoring engine ----
    score = 0
    if roe > 12:
        score += 2
    if 0 <= debt_to_equity < 1.0:
        score += 2
    if revenue_growth > 15:
        score += 2
    if volume_shock > 1.5:
        score += 2
    score += max(sentiment_score, 0)  # only positive sentiment adds points
    if sentiment_score < 0:
        score -= 2  # penalize negative-news stocks directly

    if score >= 9:
        verdict = "🔥 STRONG BUY (Institutional Entry Detected)"
    elif score >= 6:
        verdict = "⏳ ACCUMULATE (Good for Watchlist)"
    elif debt_to_equity > 1.5 or sentiment_score < 0:
        verdict = "❌ AVOID (Risk Flag)"
    else:
        verdict = "👀 HOLD / WAIT (Weak Momentum)"

    return {
        "Stock": ticker,
        "Live Price (₹)": round(price, 2),
        "Market Cap (Cr)": round(mcap, 2),
        "ROE (%)": round(roe, 2),
        "Debt/Equity": round(debt_to_equity, 2),
        "Revenue Growth (%)": round(revenue_growth, 2),
        "Volume Spike": f"{round(volume_shock, 1)}x",
        "Detected Catalyst": catalyst,
        "Score": score,
        "AI Action Verdict": verdict,
    }


def style_verdict(val):
    if "STRONG BUY" in val:
        return "background-color: #d4f7d4; color: #0a5d0a; font-weight: 600;"
    if "ACCUMULATE" in val:
        return "background-color: #fff6cc; color: #7a5c00; font-weight: 600;"
    if "AVOID" in val:
        return "background-color: #f8d4d4; color: #7a0a0a; font-weight: 600;"
    return "background-color: #eaeaea; color: #444;"


if scan_clicked:
    if not auto_universe:
        st.error("Please provide at least one ticker in the scan universe.")
    else:
        results = []
        failed = []

        progress_bar = st.progress(0, text="Starting scan...")
        total = len(auto_universe)
        completed = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_ticker = {
                executor.submit(fetch_stock_data, ticker): ticker for ticker in auto_universe
            }
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                completed += 1
                progress_bar.progress(
                    completed / total, text=f"Scanned {completed}/{total} — {ticker}"
                )
                try:
                    results.append(future.result())
                except Exception as e:
                    failed.append((ticker, str(e)))

        progress_bar.empty()

        if failed:
            with st.expander(f"⚠️ {len(failed)} stock(s) skipped due to errors"):
                for ticker, reason in failed:
                    st.write(f"- **{ticker}**: {reason}")

        if results:
            df = pd.DataFrame(results)

            st.subheader("📊 Top AI Recommendations (Sorted by Best Opportunities)")

            sort_rank = {"STRONG BUY": 0, "ACCUMULATE": 1, "HOLD": 2, "AVOID": 3}
            df['sort_order'] = df['AI Action Verdict'].apply(
                lambda x: next((v for k, v in sort_rank.items() if k in x), 4)
            )
            df = df.sort_values(['sort_order', 'Score'], ascending=[True, False]).drop(columns=['sort_order'])

            # pandas >= 2.1 renamed Styler.applymap -> Styler.map; support both
            styler = df.style
            if hasattr(styler, "map"):
                styled_df = styler.map(style_verdict, subset=['AI Action Verdict'])
            else:
                styled_df = styler.applymap(style_verdict, subset=['AI Action Verdict'])
            st.dataframe(styled_df, use_container_width=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Strong Buys", int(df['AI Action Verdict'].str.contains('STRONG BUY').sum()))
            c2.metric("Accumulate", int(df['AI Action Verdict'].str.contains('ACCUMULATE').sum()))
            c3.metric("Avoid", int(df['AI Action Verdict'].str.contains('AVOID').sum()))

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Live Strategy Sheet 📥", data=csv, file_name="AI_Live_Signals.csv", mime="text/csv")
        else:
            st.error("No data could be fetched for any ticker. Check your network/ticker list and try again.")
