import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI Multibagger Scanner", layout="centered")
st.title("🔥 AI Multibagger Stock Scanner")
st.write("Mobile-Friendly Real-time Dashboard")

default_stocks = "KAYNES.NS, DATAPATTERNS.NS, INOXWIND.NS, HBLPOWER.NS, TATAPOWER.NS"
user_input = st.text_input("Stocks ke Tickers dalein (comma separated):", default_stocks)

if st.button("Scan Now 🚀"):
    tickers = [t.strip() for t in user_input.split(",")]
    multibagger_picks = []
    
    with st.spinner("Fetching live market data..."):
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                roe = info.get('returnOnEquity', 0) * 100
                debt_to_equity = info.get('debtToEquity', 0)
                if debt_to_equity > 10:  
                    debt_to_equity = debt_to_equity / 100
                revenue_growth = info.get('revenueGrowth', 0) * 100
                price = info.get('currentPrice', info.get('previousClose', 0))
                
                status = "❌ Avoid"
                if roe > 15 and debt_to_equity < 1.0 and revenue_growth > 15:
                    status = "🔥 Potential Multibagger"
                elif roe > 10 and debt_to_equity < 1.5:
                    status = "👀 Watchlist"
                
                multibagger_picks.append({
                    "Stock": ticker,
                    "Price (₹)": price,
                    "ROE (%)": round(roe, 2),
                    "Debt/Equity": round(debt_to_equity, 2),
                    "Growth (%)": round(revenue_growth, 2),
                    "AI Verdict": status
                })
            except:
                pass
                
    if multibagger_picks:
        df = pd.DataFrame(multibagger_picks)
        st.dataframe(df, use_container_width=True)
