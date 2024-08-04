import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

def analyze_stocks(tickers):
    results = []
    
    for ticker in tickers:
        # Fetch historical data
        stock = yf.Ticker(ticker)
        df = stock.history(period="1mo")
        
        # Calculate RSI
        rsi_indicator = RSIIndicator(close=df['Close'], window=14)
        df['RSI'] = rsi_indicator.rsi()
        
        # Calculate EMA5 and EMA20
        ema5_indicator = EMAIndicator(close=df['Close'], window=5)
        ema20_indicator = EMAIndicator(close=df['Close'], window=20)
        df['EMA5'] = ema5_indicator.ema_indicator()
        df['EMA20'] = ema20_indicator.ema_indicator()
        
        # Identify buy and sell candles
        df['Buy'] = (df['Close'] > df['Open']) & (df['RSI'] < 70)
        df['Sell'] = df['Close'] < df['Open']
        
        # Check for EMA5 crossing above EMA20 in the last 2 days
        df['EMA_Cross'] = (df['EMA5'] > df['EMA20']) & (df['EMA5'].shift(1) <= df['EMA20'].shift(1))
        recent_cross = df['EMA_Cross'].iloc[-2:].any()
        
        # Find the most recent buy candle
        latest_buy = df[df['Buy']].iloc[-1] if not df[df['Buy']].empty else None
        
        if latest_buy is not None and recent_cross:
            # Find the previous sell candle
            prev_sell = df[df['Sell'] & (df.index < latest_buy.name)].iloc[-1] if not df[df['Sell'] & (df.index < latest_buy.name)].empty else None
            
            if prev_sell is not None:
                buy_size = latest_buy['Close'] - latest_buy['Open']
                sell_size = prev_sell['Open'] - prev_sell['Close']
                
                if buy_size > sell_size:
                    results.append({
                        'Ticker': ticker,
                        'Date': latest_buy.name,
                        'Buy Size': buy_size,
                        'Sell Size': sell_size,
                        'RSI': latest_buy['RSI'],
                        'EMA5': latest_buy['EMA5'],
                        'EMA20': latest_buy['EMA20']
                    })
    
    return results

# Streamlit app
st.title('Advanced Stock Scanner')

# User input
user_input = st.text_input("Enter stock tickers separated by commas:", "AAPL,MSFT,GOOGL")

# Analysis button
if st.button('Analyze Stocks'):
    # Parse input and analyze stocks
    tickers = [ticker.strip() for ticker in user_input.split(',')]
    
    with st.spinner('Analyzing stocks...'):
        results = analyze_stocks(tickers)

    # Display results
    if results:
        st.subheader("Stocks meeting the following criteria:")
        st.write("1. Recent buy candle larger than previous sell candle")
        st.write("2. RSI below 70")
        st.write("3. EMA5 crossed above EMA20 in the last 2 days")
        for result in results:
            st.write(f"**Ticker:** {result['Ticker']}")
            st.write(f"**Date:** {result['Date']}")
            st.write(f"**Buy Candle Size:** {result['Buy Size']:.2f}")
            st.write(f"**Previous Sell Candle Size:** {result['Sell Size']:.2f}")
            st.write(f"**RSI:** {result['RSI']:.2f}")
            st.write(f"**EMA5:** {result['EMA5']:.2f}")
            st.write(f"**EMA20:** {result['EMA20']:.2f}")
            st.write("---")
    else:
        st.info("No stocks found matching the criteria.")

# Add some information about the app
st.sidebar.header("About")
st.sidebar.info(
    "This app scans user-inputted stock tickers to find stocks that meet the following criteria:\n\n"
    "1. The most recent buy candle is larger than the previous sell candle\n"
    "2. RSI is below 70\n"
    "3. EMA5 has crossed above EMA20 in the last 2 days\n\n"
    "Enter stock tickers separated by commas and click 'Analyze Stocks' to start."
)

# Add a footer
st.sidebar.markdown("---")
st.sidebar.markdown("Created with Streamlit")
