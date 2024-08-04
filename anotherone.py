
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
    # Download data
    data = yf.download(symbol, start=start_date, end=end_date)
    
    # Calculate indicators
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()
    
    macd = MACD(data['Close'])
    data['MACD'] = macd.macd()
    data['MACD_Signal'] = macd.macd_signal()
    
    rsi = RSIIndicator(data['Close'])
    data['RSI'] = rsi.rsi()
    
    bb = BollingerBands(data['Close'])
    data['BB_Upper'] = bb.bollinger_hband()
    data['BB_Lower'] = bb.bollinger_lband()
    
    # Generate buy signals
    data['Buy_Signal'] = 0
    data.loc[(data['SMA_50'] > data['SMA_200']) &
             (data['MACD'] > data['MACD_Signal']) &
             (data['RSI'] < 70) &
             (data['Close'] < data['BB_Lower']), 'Buy_Signal'] = 1
    
    # Calculate entry and exit prices
    data['Entry_Price'] = np.where(data['Buy_Signal'] == 1, data['Close'], np.nan)
    data['Exit_Price'] = np.where(data['Buy_Signal'].shift(1) == 1, data['Close'], np.nan)
    
    return data

def plot_stock_data(data, symbol):
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Candlestick'))
    
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_50'], name='SMA 50'))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_200'], name='SMA 200'))
    
    buy_signals = data[data['Buy_Signal'] == 1]
    fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'], 
                             mode='markers', name='Buy Signal',
                             marker=dict(symbol='triangle-up', size=10, color='green')))
    
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
                st.write(f"Buy Signal on {index.date()}:")
                st.write(f"Entry Price: ${row['Entry_Price']:.2f}")
                exit_price = signals.loc[signals.index > index, 'Exit_Price'].first_valid_index()
                if exit_price:
                    st.write(f"Exit Price: ${signals.loc[exit_price, 'Exit_Price']:.2f}")
                else:
                    st.write("Exit Price: Not available (hold position)")
                st.write("")

# Streamlit app
st.title("Stock Analysis App")

# User inputs
symbols_input = st.text_input("Enter stock symbols separated by commas (e.g., AAPL,MSFT,GOOGL)")
start_date = st.date_input("Start date", date.today() - timedelta(days=365))
end_date = st.date_input("End date", date.today())

if st.button("Analyze"):
    if symbols_input:
        symbols = [symbol.strip() for symbol in symbols_input.split(',')]
        analyze_stocks(symbols, start_date, end_date)
    else:
        st.warning("Please enter at least one stock symbol.")