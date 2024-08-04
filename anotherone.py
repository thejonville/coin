import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

def analyze_stocks(tickers):
    results = []
    
    for ticker in tickers:
        # Fetch historical data
        stock = yf.Ticker(ticker)
        df = stock.history(period="1mo")
        
        # Calculate RSI
        rsi_indicator = RSIIndicator(close=df['Close'], window=14)
        df['RSI'] = rsi_indicator.rsi()
        
        # Identify buy and sell candles
        df['Buy'] = (df['Close'] > df['Open']) & (df['RSI'] < 70)
        df['Sell'] = df['Close'] < df['Open']
        
        # Find the most recent buy candle
        latest_buy = df[df['Buy']].iloc[-1] if not df[df['Buy']].empty else None
        
        if latest_buy is not None:
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
                        'RSI': latest_buy['RSI']
                    })
    
    return results

# Streamlit app
st.title('Stock Scanner')

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
        st.subheader("Stocks with recent buy candles larger than previous sell candles and RSI below 70:")
        for result in results:
            st.write(f"**Ticker:** {result['Ticker']}")
            st.write(f"**Date:** {result['Date']}")
            st.write(f"**Buy Candle Size:** {result['Buy Size']:.2f}")
            st.write(f"**Previous Sell Candle Size:** {result['Sell Size']:.2f}")
            st.write(f"**RSI:** {result['RSI']:.2f}")
            st.write("---")
    else:
        st.info("No stocks found matching the criteria.")

# Add some information about the app
st.sidebar.header("About")
st.sidebar.info(
    "This app scans user-inputted stock tickers to find the most recent buy "
    "candles that are larger than the previous sell candle and have an RSI below 70. "
    "Enter stock tickers separated by commas and click 'Analyze Stocks' to start."
)

# Add a footer
st.sidebar.markdown("---")
st.sidebar.markdown("Created with Streamlit")
