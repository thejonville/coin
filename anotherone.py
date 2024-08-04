import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import matplotlib.pyplot as plt
import io

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
                        'Date': latest_buy.name.date(),
                        'Buy Size': round(buy_size, 2),
                        'Sell Size': round(sell_size, 2),
                        'RSI': round(latest_buy['RSI'], 2),
                        'EMA5': round(latest_buy['EMA5'], 2),
                        'EMA20': round(latest_buy['EMA20'], 2),
                        'Volume': int(latest_buy['Volume'])
                    })
    
    return results

def plot_stock(ticker):
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
    
    # Plot the data
    fig, ax = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Price and EMA plot
    ax[0].plot(df.index, df['Close'], label='Close Price')
    ax[0].plot(df.index, df['EMA5'], label='EMA5')
    ax[0].plot(df.index, df['EMA20'], label='EMA20')
    ax[0].set_title(f'{ticker} Price and EMA')
    ax[0].legend()
    
    # RSI plot
    ax[1].plot(df.index, df['RSI'], label='RSI')
    ax[1].axhline(70, color='r', linestyle='--')
    ax[1].axhline(30, color='r', linestyle='--')
    ax[1].set_title('RSI')
    ax[1].legend()
    
    plt.tight_layout()
    
    return fig

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
        
        # Convert results to DataFrame
        df_results = pd.DataFrame(results)
        
        # Display results table
        st.dataframe(df_results)
        
        # Allow user to select a stock
        selected_ticker = st.selectbox("Select a stock to view chart", df_results['Ticker'])
        
        if selected_ticker:
            fig = plot_stock(selected_ticker)
            st.pyplot(fig)
            
            # Download button
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            st.download_button(
                label="Download chart as PNG",
                data=buf,
                file_name=f"{selected_ticker}_chart.png",
                mime="image/png"
            )
        
    else:
        st.info("No stocks found matching the criteria.")

# Add some information about the app
st.sidebar.header("About")
st.sidebar.info(
    "This app scans user-inputted stock tickers to find stocks that meet the following criteria:\n\n"
    "1. The most recent buy candle is larger than the previous sell candle\n"
    "2. RSI below 70\n"
    "3. EMA5 has crossed above EMA20 in the last 2 days\n\n"
    "Enter stock tickers separated by commas and click 'Analyze Stocks' to start."
)

# Add a footer
st.sidebar.markdown("---")
st.sidebar.markdown("Created with Streamlit")
