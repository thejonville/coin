
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import plotly.graph_objects as go
from datetime import date, timedelta

def get_signals(symbol, start_date, end_date, stop_loss_pct=0.02, profit_target_pct=0.05):
    # Download data
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
    data['BB_Lower'] = bb.bollinger_lband()
    
    # Generate buy signals and exit prices
    data['Buy_Signal'] = 0
    data['Exit_Signal'] = 0
    data['Entry_Price'] = np.nan
    data['Exit_Price'] = np.nan
    data['Exit_Reason'] = ''
    
    in_position = False
    entry_price = 0
    
    for i in range(1, len(data)):
        if not in_position:
            if (data.iloc[i]['SMA_5'] > data.iloc[i]['SMA_20']) and \
               (data.iloc[i]['MACD'] > data.iloc[i]['MACD_Signal']) and \
               (data.iloc[i]['RSI'] < 60) and (data.iloc[i]['Close'] < data.iloc[i]['BB_Lower']):
                data.iloc[i, data.columns.get_loc('Buy_Signal')] = 1
                data.iloc[i, data.columns.get_loc('Entry_Price')] = data.iloc[i]['Close']
                in_position = True
                entry_price = data.iloc[i]['Close']
        else:
            current_price = data.iloc[i]['Close']
            if current_price <= entry_price * (1 - stop_loss_pct):
                data.iloc[i, data.columns.get_loc('Exit_Signal')] = 1
                data.iloc[i, data.columns.get_loc('Exit_Price')] = current_price
                data.iloc[i, data.columns.get_loc('Exit_Reason')] = 'Stop Loss'
                in_position = False
            elif current_price >= entry_price * (1 + profit_target_pct):
                data.iloc[i, data.columns.get_loc('Exit_Signal')] = 1
                data.iloc[i, data.columns.get_loc('Exit_Price')] = current_price
                data.iloc[i, data.columns.get_loc('Exit_Reason')] = 'Profit Target'
                in_position = False
            elif data.iloc[i]['RSI'] > 70:
                data.iloc[i, data.columns.get_loc('Exit_Signal')] = 1
                data.iloc[i, data.columns.get_loc('Exit_Price')] = current_price
                data.iloc[i, data.columns.get_loc('Exit_Reason')] = 'RSI Overbought'
                in_position = False
    
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
        exit_signals = signals[signals['Exit_Signal'] == 1]
        
        if buy_signals.empty:
            st.write("No buy signals generated for this stock in the given time period.")
        else:
            for i, (buy_index, buy_row) in enumerate(buy_signals.iterrows()):
                st.write(f"Trade {i+1}:")
                st.write(f"Buy Signal on {buy_index}:")
                st.write(f"Entry Price: ${buy_row['Entry_Price']:.2f}")
                
                # Find the next exit signal after this buy signal
                next_exit = exit_signals[exit_signals.index > buy_index].iloc[0] if not exit_signals[exit_signals.index > buy_index].empty else None
                
                if next_exit is not None:
                    st.write(f"Exit Signal on {next_exit.name}:")
                    st.write(f"Exit Price: ${next_exit['Exit_Price']:.2f} ({next_exit['Exit_Reason']})")
                    profit_loss = (next_exit['Exit_Price'] - buy_row['Entry_Price']) / buy_row['Entry_Price'] * 100
                    st.write(f"Profit/Loss: {profit_loss:.2f}%")
                else:
                    st.write("No exit signal generated (hold position)")
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
