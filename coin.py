
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

from prophet import Prophet

def get_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date, interval="1d")
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)  # Remove timezone information
    return df[['Date', 'Close', 'Volume']]

def forecast_with_prophet(df, periods=30):
    if not prophet_available:
        return None
    
    try:
        prophet_df = df[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})
        prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
        prophet_df['y'] = prophet_df['y'].astype(np.float64)
        
        model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        return forecast
    except Exception as e:
        st.error(f"Error in Prophet forecasting: {str(e)}")
        return None

def calculate_indicators(df):
    # Calculate MACD
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Calculate RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Calculate Moving Averages
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()

    return df

def check_buy_signal(row):
    price_trend = row['Close'] > row['Close_prev']
    short_term_trend = row['MA5'] > row['MA20']
    long_term_trend = row['MA50'] > row['MA200']
    macd_crossover = (row['MACD'] > row['Signal_Line']) and (row['MACD_prev'] <= row['Signal_Line_prev'])
    unusual_volume = row['Volume'] > 1.5 * row['Avg_Volume']
    rsi_below_50 = row['RSI'] < 50
    
    return price_trend and short_term_trend and long_term_trend and macd_crossover and unusual_volume and rsi_below_50

def backtest_strategy(df):
    df = calculate_indicators(df)
    
    # Calculate previous day's values for comparison
    df['Close_prev'] = df['Close'].shift(1)
    df['MACD_prev'] = df['MACD'].shift(1)
    df['Signal_Line_prev'] = df['Signal_Line'].shift(1)
    df['Avg_Volume'] = df['Volume'].rolling(window=20).mean()
    
    # Generate buy signals
    df['Signal'] = df.apply(check_buy_signal, axis=1).astype(int)
    
    # Calculate returns
    df['Return'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Return']
    
    # Calculate cumulative returns
    df['Cumulative_Market_Return'] = (1 + df['Return']).cumprod()
    df['Cumulative_Strategy_Return'] = (1 + df['Strategy_Return']).cumprod()
    
    # Calculate performance metrics
    total_return = df['Cumulative_Strategy_Return'].iloc[-1] - 1
    market_return = df['Cumulative_Market_Return'].iloc[-1] - 1
    sharpe_ratio = np.sqrt(252) * df['Strategy_Return'].mean() / df['Strategy_Return'].std()
    
    # Calculate win rate
    trades = df[df['Signal'].diff() == 1]
    winning_trades = trades[trades['Return'] > 0]
    win_rate = len(winning_trades) / len(trades) if len(trades) > 0 else 0

    return total_return, market_return, sharpe_ratio, win_rate

def main():
    st.title("Stock Analysis with Technical Indicators")
    
    if not prophet_available:
        st.warning("Prophet is not available. Forecasting will not be performed.")
    
    tickers = st.text_input("Enter stock tickers separated by commas (e.g., AAPL, MSFT, GOOGL):")
    
    if tickers:
        tickers = [ticker.strip().upper() for ticker in tickers.split(',')]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        for ticker in tickers:
            try:
                st.write(f"Analyzing {ticker}...")
                df = get_stock_data(ticker, start_date, end_date)
                
                # Backtest the strategy
                total_return, market_return, sharpe_ratio, win_rate = backtest_strategy(df)
                
                st.write(f"Backtest results for {ticker}:")
                st.write(f"Strategy Total Return: {total_return * 100:.2f}%")
                st.write(f"Market Total Return: {market_return * 100:.2f}%")
                st.write(f"Sharpe Ratio: {sharpe_ratio:.2f}")
                st.write(f"Win Rate: {win_rate * 100:.2f}%")
                
                # Forecast (if Prophet is available)
                if prophet_available:
                    forecast = forecast_with_prophet(df)
                    if forecast is not None:
                        st.write("Forecast for next 30 days:")
                        st.line_chart(forecast[['ds', 'yhat']])
                
            except Exception as e:
                st.write(f"Error analyzing {ticker}: {str(e)}")

if __name__ == "__main__":
    main()
