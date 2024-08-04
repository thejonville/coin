
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import plotly.graph_objects as go
from datetime import date, timedelta

def get_signals(symbol, start_date, end_date):
    # Download data (consider using intraday data for very short-term trading)
    data = yf.download(symbol, start=start_date, end=end_date, interval="1h")
    
    # Calculate indicators
    data['SMA_5'] = data['Close'].rolling(window=5).mean()
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    
    macd = MACD(data['Close'], window_slow=26, window_fast=12, window_sign=9)
    data['MACD'] = macd.macd()
    data['MACD_Signal'] = macd.macd_signal()
    
    rsi = RSIIndicator(data['Close'], window=7)
    data['RSI'] = rsi.rsi()
    
    bb = BollingerBands(data['Close'], window=10)
    data['BB_Upper'] = bb.bollinger_hband()
    data['BB_Lower'] = bb.bollinger_lband()
    
    # Generate buy signals
    data['Buy_Signal'] = 0
    data.loc[(data['SMA_5'] > data['SMA_20']) &
             (data['MACD'] > data['MACD_Signal']) &
             (data['RSI'] < 60) &  # Less strict RSI condition
             (data['Close'] < data['BB_Lower']), 'Buy_Signal'] = 1
    
    # Simple short-term exit strategy (exit after 5 periods or when RSI > 70)
    data['Exit_Signal'] = 0
    data.loc[(data['Buy_Signal'].rolling(window=5).sum() > 0) | (data['RSI'] > 70), 'Exit_Signal'] = 1
    
    return data

def plot_stock_data(data, symbol):
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Candlestick'))
    
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_5'], name='SMA 5'))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name='SMA 20'))
    
    buy_signals = data[data['Buy_Signal'] == 1]
    fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'], 
                             mode='markers', name='Buy Signal',
                             marker=dict(symbol='triangle-up', size=10, color='green')))
    
    exit_signals = data[data['Exit_Signal'] == 1]
    fig.add_trace(go.Scatter(x=exit_signals.index, y=exit_signals['Close'], 
                             mode='markers', name='Exit Signal',
                             marker=dict(symbol='triangle-down', size=10, color='red')))
    
    fig.update_layout(title=f'{symbol} Stock Price', xaxis_title='Date', yaxis_title='Price')
    return fig

def analyze_stocks(symbols, start_date, end_date):
    for symbol in symbols:
        st.subheader(f"Analysis for {symbol}")
        
        signals = get_signals(symbol, start_date, end_date)
        
        # Plot stock data
        st.plotly_chart(plot_stock_data(signals, symbol))
        
        # Print buy signals, entry prices, and exit prices
        buy_signals = signals[signals['Buy_Signal'] == 1]
        if buy_signals.empty:
            st.write("No buy signals generated for this stock in the given time period.")
        else:
            for index, row in buy_signals.iterrows():
                st.write(f"Buy Signal on {index}:")
                st.write(f"Entry Price: ${row['Close']:.2f}")
                exit_signal = signals.loc[signals.index > index, 'Exit_Signal'].first_valid_index()
                if exit_signal:
                    st.write(f"Exit Price: ${signals.loc[exit_signal, 'Close']:.2f} on {exit_signal}")
                else:
                    st.write("Exit Price: Not available (hold position)")
                st.write("")

# Streamlit app
st.title("Short-Term Stock Analysis App")

# User inputs
symbols_input = st.text_input("Enter stock symbols separated by commas (e.g., AAPL,MSFT,GOOGL)")
start_date = st.date_input("Start date", date.today() - timedelta(days=30))
end_date = st.date_input("End date", date.today())

if st.button("Analyze"):
    if symbols_input:
        symbols = [symbol.strip() for symbol in symbols_input.split(',')]
        analyze_stocks(symbols, start_date, end_date)
    else:
        st.warning("Please enter at least one stock symbol.")