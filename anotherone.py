import streamlit as st
import yfinance as yf
import pandas as pd
import ta

def get_stock_data(ticker, period='1y'):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    return df

def add_indicators(df):
    # Add 50-day and 200-day moving averages
    df['SMA50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['SMA200'] = ta.trend.sma_indicator(df['Close'], window=200)
    
    # Add Relative Strength Index (RSI)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # Add Moving Average Convergence Divergence (MACD)
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    
    # Add Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['Close'])
    df['BB_Upper'] = bollinger.bollinger_hband()
    df['BB_Lower'] = bollinger.bollinger_lband()
    
    return df

def generate_signals(df):
    signals = []
    
    # Golden Cross / Death Cross
    if df['SMA50'].iloc[-1] > df['SMA200'].iloc[-1] and df['SMA50'].iloc[-2] <= df['SMA200'].iloc[-2]:
        signals.append("BUY: Golden Cross (50-day SMA crossed above 200-day SMA)")
    elif df['SMA50'].iloc[-1] < df['SMA200'].iloc[-1] and df['SMA50'].iloc[-2] >= df['SMA200'].iloc[-2]:
        signals.append("SELL: Death Cross (50-day SMA crossed below 200-day SMA)")
    
    # RSI Overbought/Oversold
    if df['RSI'].iloc[-1] > 70:
        signals.append("SELL: RSI Overbought (above 70)")
    elif df['RSI'].iloc[-1] < 30:
        signals.append("BUY: RSI Oversold (below 30)")
    
    # MACD Crossover
    if df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['MACD_Signal'].iloc[-2]:
        signals.append("BUY: MACD crossed above Signal Line")
    elif df['MACD'].iloc[-1] < df['MACD_Signal'].iloc[-1] and df['MACD'].iloc[-2] >= df['MACD_Signal'].iloc[-2]:
        signals.append("SELL: MACD crossed below Signal Line")
    
    # Bollinger Bands
    if df['Close'].iloc[-1] > df['BB_Upper'].iloc[-1]:
        signals.append("SELL: Price above Upper Bollinger Band")
    elif df['Close'].iloc[-1] < df['BB_Lower'].iloc[-1]:
        signals.append("BUY: Price below Lower Bollinger Band")
    
    return signals

st.title("Stock Buy/Sell Signal Generator")

# User input for stock tickers
tickers_input = st.text_input("Enter stock tickers separated by commas (e.g., AAPL,MSFT,GOOGL):")
tickers = [ticker.strip() for ticker in tickers_input.split(',') if ticker.strip()]

if tickers:
    for ticker in tickers:
        st.subheader(f"Analysis for {ticker}")
        
        df = get_stock_data(ticker)
        df = add_indicators(df)
        signals = generate_signals(df)
        
        if signals:
            for signal in signals:
                st.write(signal)
        else:
            st.write("No clear buy or sell signals at the moment.")
        
        # Display recent price and indicator values
        st.write(f"Recent closing price: ${df['Close'].iloc[-1]:.2f}")
        st.write(f"50-day SMA: ${df['SMA50'].iloc[-1]:.2f}")
        st.write(f"200-day SMA: ${df['SMA200'].iloc[-1]:.2f}")
        st.write(f"RSI: {df['RSI'].iloc[-1]:.2f}")
        st.write(f"MACD: {df['MACD'].iloc[-1]:.2f}")
        st.write(f"MACD Signal: {df['MACD_Signal'].iloc[-1]:.2f}")
        
        st.line_chart(df[['Close', 'SMA50', 'SMA200']])
        
        st.write("---")
else:
    st.write("Please enter at least one stock ticker to analyze.")
