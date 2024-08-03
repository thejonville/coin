import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_macd(data):
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_adx(data, period=14):
    high = data['High']
    low = data['Low']
    close = data['Close']
    
    plus_dm = high.diff()
    minus_dm = low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    tr = pd.concat([tr1, tr2, tr3], axis=1, join='inner').max(axis=1)
    
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / atr)
    minus_di = abs(100 * (minus_dm.ewm(alpha=1/period).mean() / atr))
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.ewm(alpha=1/period).mean()
    
    return adx

def check_macd_and_adx(ticker):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)  # Get 60 days of data for calculation
    
    data = yf.download(ticker, start=start_date, end=end_date)
    if len(data) < 27:  # We need at least 27 days of data for MACD calculation
        return False, "Insufficient data"
    
    macd, signal = calculate_macd(data)
    adx = calculate_adx(data)
    
    # Check last 2 days for MACD crossing above signal line
    last_two_days = macd.tail(2)
    last_two_days_signal = signal.tail(2)
    last_adx = adx.tail(1).values[0]
    
    if len(last_two_days) < 2 or len(last_two_days_signal) < 2:
        return False, "Insufficient recent data"
    
    if (last_two_days.iloc[0] <= last_two_days_signal.iloc[0] and 
        last_two_days.iloc[1] > last_two_days_signal.iloc[1] and
        last_adx >= 20):
        # Calculate the strength of the crossing
        crossing_strength = (last_two_days.iloc[1] - last_two_days_signal.iloc[1]) / last_two_days_signal.iloc[1]
        if crossing_strength > 0.01:  # 1% threshold for "strong" crossing
            return True, f"MACD Crossing: Yes, ADX: {last_adx:.2f}"
    
    return False, f"MACD Crossing: No, ADX: {last_adx:.2f}"

st.title('Stock Scanner: MACD Crossing & ADX')

# User input
tickers_input = st.text_input("Enter stock tickers separated by commas:", "AAPL,MSFT,GOOGL")
tickers = [ticker.strip().upper() for ticker in tickers_input.split(',')]

if st.button('Scan Stocks'):
    results = []
    for ticker in tickers:
        try:
            signal, details = check_macd_and_adx(ticker)
            status = "Potential Buy" if signal else "No Signal"
            results.append({"Ticker": ticker, "Status": status, "Details": details})
        except Exception as e:
            results.append({"Ticker": ticker, "Status": "Error", "Details": str(e)})
    
    # Display results
    st.subheader("Scan Results")
    df = pd.DataFrame(results)
    st.dataframe(df)
    
    # Display potential buy signals
    potential_buys = df[df['Status'] == 'Potential Buy']
    if not potential_buys.empty:
        st.subheader("Potential Buy Signals")
        st.dataframe(potential_buys)
    else:
        st.write("No potential buy signals detected.")

st.markdown("""
### About this Stock Scanner
This tool scans for stocks that show a potential buy signal based on two criteria:
1. A strong MACD (Moving Average Convergence Divergence) crossing above the signal line in the last 2 days.
2. An ADX (Average Directional Index) value of 20 or above, indicating a strong trend.
