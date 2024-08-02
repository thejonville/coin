import yfinance as yf
from prophet import Prophet
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

def get_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date, interval="1d")
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)  # Remove timezone information
    return df[['Date', 'Close', 'Volume']]

def forecast_with_prophet(df, periods=30):
    prophet_df = df[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
    prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
    prophet_df['y'] = prophet_df['y'].astype(np.float64)
    
    model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    return forecast

def calculate_macd(df, short_period=12, long_period=26, signal_period=9):
    df['EMA_short'] = df['Close'].ewm(span=short_period, adjust=False).mean()
    df['EMA_long'] = df['Close'].ewm(span=long_period, adjust=False).mean()
    df['MACD'] = df['EMA_short'] - df['EMA_long']
    df['Signal_Line'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
    return df

def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def check_bullish_trend(df, forecast):
    # Check if the forecasted price is higher than the current price
    current_price = df['Close'].iloc[-1]
    forecasted_price = forecast['yhat'].iloc[-1]
    price_trend = forecasted_price > current_price

    # Calculate 5-day, 20-day, 50-day, and 200-day moving averages
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()

    # Check if 5-day MA is above 20-day MA
    short_term_trend = df['MA5'].iloc[-1] > df['MA20'].iloc[-1]

    # Check if 50-day MA is above 200-day MA (Golden Cross)
    long_term_trend = df['MA50'].iloc[-1] > df['MA200'].iloc[-1]

    # Calculate MACD and check for crossover
    df = calculate_macd(df)
    macd_crossover = (df['MACD'].iloc[-1] > df['Signal_Line'].iloc[-1]) and (df['MACD'].iloc[-2] <= df['Signal_Line'].iloc[-2])

    # Check for unusual volume in the last 2 days
    avg_volume = df['Volume'].rolling(window=20).mean()
    unusual_volume = (df['Volume'].iloc[-1] > 1.5 * avg_volume.iloc[-1]) or (df['Volume'].iloc[-2] > 1.5 * avg_volume.iloc[-2])

    # Calculate RSI and check if it's less than 50
    df = calculate_rsi(df)
    rsi_below_50 = df['RSI'].iloc[-1] < 50

    return price_trend, short_term_trend, long_term_trend, macd_crossover, unusual_volume, rsi_below_50

def backtest_strategy(df):
    df = calculate_macd(df)
    df = calculate_rsi(df)
    
    # Initialize columns for signals and returns
    df['Signal'] = 0
    df['Return'] = 0.0
    
    # Generate buy signals based on criteria
    for i in range(len(df)):
        if i < 1:  # Skip the first row
            continue
        
        price_trend = df['Close'].iloc[i] > df['Close'].iloc[i-1]
        short_term_trend = df['MA5'].iloc[i] > df['MA20'].iloc[i]
        long_term_trend = df['MA50'].iloc[i] > df['MA200'].iloc[i]
        macd_crossover = (df['MACD'].iloc[i] > df['Signal_Line'].iloc[i]) and (df['MACD'].iloc[i-1] <= df['Signal_Line'].iloc[i-1])
        avg_volume = df['Volume'].rolling(window=20).mean().iloc[i]
        unusual_volume = (df['Volume'].iloc[i] > 1.5 * avg_volume)
        rsi_below_50 = df['RSI'].iloc[i] < 50
        
        if price_trend and short_term_trend and long_term_trend and macd_crossover and unusual_volume and rsi_below_50:
            df['Signal'].iloc[i] = 1  # Buy signal
    
    # Calculate returns based on signals
    for i in range(1, len(df)):
        if df['Signal'].iloc[i-1] == 1:
            df['Return'].iloc[i] = (df['Close'].iloc[i] / df['Close'].iloc[i-1]) - 1
    
    # Calculate cumulative returns
    df['Cumulative_Return'] = (1 + df['Return']).cumprod() - 1
    
    # Calculate performance metrics
    total_return = df['Cumulative_Return'].iloc[-1]
    win_rate = df[df['Return'] > 0].shape[0] / df[df['Signal'] == 1].shape[0] if df[df['Signal'] == 1].shape[0] > 0 else 0
    
    return total_return, win_rate

def main():
    st.title("Stock Analysis with Prophet and Technical Indicators")
    
    tickers = st.text_input("Enter stock tickers separated by commas (e.g., AAPL, MSFT, GOOGL):")
    
    if tickers:
        tickers = [ticker.strip().upper() for ticker in tickers.split(',')]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        bullish_stocks = []

        for ticker in tickers:
            try:
                st.write(f"Analyzing {ticker}...")
                df = get_stock_data(ticker, start_date, end_date)
                forecast = forecast_with_prophet(df)
                
                price_trend, short_term_trend, long_term_trend, macd_crossover, unusual_volume, rsi_below_50 = check_bullish_trend(df, forecast)
                
                if price_trend and short_term_trend and long_term_trend and macd_crossover and unusual_volume and rsi_below_50:
                    bullish_stocks.append(ticker)
                    
                    # Backtest the strategy
                    total_return, win_rate = backtest_strategy(df)
                    st.write(f"Backtest results for {ticker}:")
                    st.write(f"Total Return: {total_return * 100:.2f}%")
                    st.write(f"Win Rate: {win_rate * 100:.2f}%")
            except Exception as e:
                st.write(f"Error analyzing {ticker}: {str(e)}")

        if bullish_stocks:
            st.write("\nStocks with potential bullish trends:")
            for stock in bullish_stocks:
                st.write(stock)
        else:
            st.write("No stocks with potential bullish trends found.")

if __name__ == "__main__":
    main()
