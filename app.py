import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI Alpha Multibagger Scanner", layout="wide")
st.title("🔥 AI Next-Gen Multibagger Stock Scanner")
st.write("Live Financial Ratios + Market Cap + Live News Sentiment Analysis")

# Default High-Growth/Turnaround Watchlist
default_stocks = "KAYNES.NS, DATAPATTERNS.NS, INOXWIND.NS, HBLPOWER.NS, TATAPOWER.NS, SUZLON.NS, IREDA.NS"
user_input = st.text_input("Stocks ke Tickers dalein (comma separated):", default_stocks)

if st.button("Run Advanced Scan 🚀"):
    tickers = [t.strip() for t in user_input.split(",")]
    multibagger_picks = []
    
    with st.spinner("Fetching financials and live market news..."):
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # 1. Price & Market Cap
                price = info.get('currentPrice', info.get('previousClose', 0))
                mcap = info.get('marketCap', 0)
                mcap_cr = mcap / 10000000 if mcap > 0 else 0
                
                if mcap_cr == 0:
                    mcap_type = "Data Missing"
                elif mcap_cr < 5000:
                    mcap_type = "🟢 Small Cap"
                elif mcap_cr < 20000:
                    mcap_type = "🟡 Mid Cap"
                else:
                    mcap_type = "🔵 Large Cap"
                
                # 2. Key Financial Ratios
                roe = info.get('returnOnEquity', 0) * 100
                debt_to_equity = info.get('debtToEquity', 0)
                if debt_to_equity > 10:  
                    debt_to_equity = debt_to_equity / 100
                revenue_growth = info.get('revenueGrowth', 0) * 100
                
                # 3. News Sentiment Analysis (Using Live Headlines)
                news = stock.news
                positive_keywords = ['order', 'profit', 'expansion', 'win', 'growth', 'deal', 'hike', 'buy', 'capex', 'multibagger']
                negative_keywords = ['loss', 'fall', 'drop', 'penalty', 'scam', 'fraud', 'investigation', 'decline', 'sell']
                
                sentiment_score = 0
                news_count = 0
                if news:
                    for item in news[:5]: # Scanning last 5 headlines
                        title = item.get('title', '').lower()
                        news_count += 1
                        for word in positive_keywords:
                            if word in title: sentiment_score += 1
                        for word in negative_keywords:
                            if word in title: sentiment_score -= 1
                
                if news_count == 0:
                    sentiment = "Neutral 😐"
                elif sentiment_score > 0:
                    sentiment = "Positive 🔥"
                elif sentiment_score < 0:
                    sentiment = "Negative ⚠️"
                else:
                    sentiment = "Neutral 😐"
                
                # 4. Multi-Criteria Smart Verdict
                if roe > 15 and debt_to_equity < 1.0 and revenue_growth > 15 and sentiment == "Positive 🔥":
                    status = "🚀 Potential Multibagger"
                elif (roe > 10 or revenue_growth > 10) and debt_to_equity < 1.5 and sentiment != "Negative ⚠️":
                    status = "⏳ Keep in Watchlist"
                elif debt_to_equity > 1.5:
                    status = "❌ Avoid (High Debt)"
                else:
                    status = "👀 Wait for Correction"
                
                multibagger_picks.append({
                    "Stock": ticker,
                    "Price (₹)": price,
                    "Market Cap (Cr)": round(mcap_cr, 2),
                    "Category": mcap_type,
                    "ROE (%)": round(roe, 2),
                    "Debt/Equity": round(debt_to_equity, 2),
                    "Growth (%)": round(revenue_growth, 2),
                    "News Sentiment": sentiment,
                    "AI Verdict": status
                })
            except:
                pass
                
    if multibagger_picks:
        df = pd.DataFrame(multibagger_picks)
        st.dataframe(df, use_container_width=True)
        
        # Download Option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report as CSV 📥", data=csv, file_name="AI_Multibagger_Report.csv", mime="text/csv")
