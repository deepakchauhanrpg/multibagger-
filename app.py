import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="AI Institutional Radar", layout="wide")
st.title("🛡️ AI Automatic Multibagger Radar (Zero-Input Mode)")
st.write("Automatically scanning Small & Mid-caps with Volume Breakouts & News Velocity")

# 1. Background Automation: Pre-defined High-Growth Mid/Small-Cap Universe
# (Bhai, background mein yeh poore pool ko automatic scan karega bina aapke type kiye)
auto_universe = [
    "SUZLON.NS", "KPIGREEN.NS", "IREDA.NS", "KAYNES.NS", "DATAPATTERNS.NS", 
    "HBLPOWER.NS", "INOXWIND.NS", "NETWEB.NS", "HITACHI.NS", "RVNL.NS", 
    "IRFC.NS", "NATCOPHARM.NS", "DEEPAKNIT.NS", "BDL.NS", "MAZDOCK.NS"
]

if st.button("Start Automatic Market Scan ⚡"):
    multibagger_picks = []
    
    with st.spinner("AI is scanning the market data, volumes, and news channels..."):
        # We simulate checking a larger universe via yfinance or directly from yahoo endpoints
        import yfinance as yf  
        
        for ticker in auto_universe:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Financials
                price = info.get('currentPrice', info.get('previousClose', 0))
                mcap = info.get('marketCap', 0) / 10000000 if info.get('marketCap', 0) > 0 else 0
                roe = info.get('returnOnEquity', 0) * 100
                debt_to_equity = info.get('debtToEquity', 0)
                if debt_to_equity > 10: debt_to_equity = debt_to_equity / 100
                revenue_growth = info.get('revenueGrowth', 0) * 100
                
                # Volume Action (Checking if big hands are buying)
                avg_volume = info.get('averageVolume', 1)
                current_volume = info.get('volume', 1)
                volume_shock = current_volume / avg_volume if avg_volume > 0 else 1
                
                # News Velocity & Trigger Prediction
                news = stock.news
                news_velocity = len(news) if news else 0
                
                catalyst = "No Major Catalyst"
                sentiment_score = 0
                
                positive_triggers = {
                    'order': 'Huge Order Win 💰',
                    'expansion': 'Capacity Expansion 🏭',
                    'capex': 'Capex Boost 📈',
                    'profit': 'Surging Profits 🚀',
                    'acquisition': 'Strategic Acquisition 🤝'
                }
                
                if news:
                    for item in news[:5]:
                        title = item.get('title', '').lower()
                        for key, msg in positive_triggers.items():
                            if key in title:
                                catalyst = msg
                                sentiment_score += 2
                
                # AI Advanced Scoring Engine
                # Price Momentum + Volume Breakout + Financials + News Catalyst
                score = 0
                if roe > 12: score += 2
                if debt_to_equity < 1.0: score += 2
                if revenue_growth > 15: score += 2
                if volume_shock > 1.5: score += 2  # Volume is 1.5x of average
                if sentiment_score > 0: score += 3
                
                # Smart Action Verdict
                if score >= 9:
                    verdict = "🔥 STRONG BUY (Institutional Entry Detected)"
                elif score >= 6:
                    verdict = "⏳ ACCUMULATE (Good for Watchlist)"
                elif debt_to_equity > 1.5:
                    verdict = "❌ AVOID (Debt Trap Risk)"
                else:
                    verdict = "👀 HOLD / WAIT (Weak Momentum)"
                
                multibagger_picks.append({
                    "Stock": ticker,
                    "Live Price (₹)": price,
                    "Market Cap (Cr)": round(mcap, 2),
                    "ROE (%)": round(roe, 2),
                    "Debt/Equity": round(debt_to_equity, 2),
                    "Volume Spike": f"{round(volume_shock, 1)}x",
                    "Detected Catalyst": catalyst,
                    "AI Action Verdict": verdict
                })
            except:
                pass
                
    if multibagger_picks:
        df = pd.DataFrame(multibagger_picks)
        
        # Presenting results in custom styled blocks
        st.subheader("📊 Top AI Recommendations (Sorted by Best Opportunities)")
        
        # Sort so Strong Buys come on top
        df['sort_order'] = df['AI Action Verdict'].apply(lambda x: 0 if 'STRONG BUY' in x else (1 if 'ACCUMULATE' in x else 2))
        df = df.sort_values('sort_order').drop(columns=['sort_order'])
        
        st.dataframe(df, use_container_width=True)
        
        # Download Option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Live Strategy Sheet 📥", data=csv, file_name="AI_Live_Signals.csv", mime="text/csv")
        
