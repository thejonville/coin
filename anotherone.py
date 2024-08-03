import streamlit as st
import yfinance as yf
import pandas as pd
import ta

def analyze_stock(ticker):
    try:
        # Fetch data
        data = yf.download(ticker, period="6mo")
        
        if len(data) < 20:  # Not enough data
            return False
        
        # Calculate indicators
        data['EMA5'] = ta.trend.ema_indicator(data['Close'], window=5)
        data['EMA20'] = ta.trend.ema_indicator(data['Close'], window=20)
        data['MACD'] = ta.trend.macd_diff(data['Close'])
        data['RSI'] = ta.momentum.rsi(data['Close'])
        
        # Check conditions
        ema_cross = (data['EMA5'].iloc[-2] <= data['EMA20'].iloc[-2]) and (data['EMA5'].iloc[-1] > data['EMA20'].iloc[-1])
        macd_cross = (data['MACD'].iloc[-2] <= 0) and (data['MACD'].iloc[-1] > 0)
        rsi_below_50 = data['RSI'].iloc[-1] < 58
        
        return ema_cross and macd_cross and rsi_below_50
    except Exception as e:
        st.error(f"Error analyzing {ticker}: {str(e)}")
        return False

st.title("Stock Screener")

# User input
tickers_input = st.text_input("Enter stock tickers (comma-separated):")
tickers = [ticker.strip().upper() for ticker in tickers_input.split(',') if ticker.strip()]

if st.button("Analyze"):
    if not tickers:
        st.warning("Please enter at least one ticker.")
    else:
        potential_buys = []
        errors = []
        
        progress_bar = st.progress(0)
        for i, ticker in enumerate(tickers):
            if analyze_stock(ticker):
                potential_buys.append(ticker)
            progress_bar.progress((i + 1) / len(tickers))
        
        if potential_buys:
            st.success("Potential buy signals found for:")
            for ticker in potential_buys:
                st.write(f"- {ticker}")
        else:
            st.info("No stocks met all the criteria.")
        
        if errors:
            st.error("Errors occurred for the following tickers:")
            for error in errors:
                st.write(error)

st.markdown("**Criteria:**")
st.markdown("- EMA5 crosses above EMA20")
st.markdown("- MACD crosses above signal line")
st.markdown("- RSI below 50")
