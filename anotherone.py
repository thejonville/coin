
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

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

def analyze_stocks(symbols, start_date, end_date):
    for symbol in symbols:
        print(f"\nAnalyzing {symbol}:")
        signals = get_signals(symbol, start_date, end_date)
        
        # Print buy signals, entry prices, and exit prices
        buy_signals = signals[signals['Buy_Signal'] == 1]
        if buy_signals.empty:
            print("No buy signals generated for this stock in the given time period.")
        else:
            for index, row in buy_signals.iterrows():
                print(f"Buy Signal on {index.date()}:")
                print(f"Entry Price: ${row['Entry_Price']:.2f}")
                exit_price = signals.loc[signals.index > index, 'Exit_Price'].first_valid_index()
                if exit_price:
                    print(f"Exit Price: ${signals.loc[exit_price, 'Exit_Price']:.2f}")
                else:
                    print("Exit Price: Not available (hold position)")
                print()

# Example usage
symbols_input = input("Enter stock symbols separated by commas (e.g., AAPL,MSFT,GOOGL): ")
symbols = [symbol.strip() for symbol in symbols_input.split(',')]
start_date = input("Enter start date (YYYY-MM-DD): ")
end_date = input("Enter end date (YYYY-MM-DD): ")

analyze_stocks(symbols, start_date, end_date)
