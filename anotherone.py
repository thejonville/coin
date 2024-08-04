import streamlit as st
import yfinance as yf
import pandas as pd

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1mo")
    return data

def filter_stocks(tickers, progress_bar):
    selected_stocks = []
    
    for i, ticker in enumerate(tickers):
        data = get_stock_data(ticker)
        data['RSI'] = calculate_rsi(data)
        
        if len(data) < 30:
            continue
        
        current_rsi = data['RSI'].iloc[-1]
        past_month_rsi = data['RSI'].tail(30)
        
        if current_rsi < 55 and (past_month_rsi >= 70).any():
            selected_stocks.append((ticker, current_rsi))
        
        progress_bar.progress((i + 1) / len(tickers))
    
    return selected_stocks

def main():
    st.title("Stock RSI Scanner")
    
    st.write("""
    This app scans user-inputted stock tickers for the following criteria:
    - Current RSI under 55
    - RSI has reached 70 or above in the past month
    """)
    
    tickers_input = st.text_input("Enter stock tickers separated by commas:")
    
    if st.button("Scan Stocks"):
        if tickers_input:
            tickers = [ticker.strip().upper() for ticker in tickers_input.split(',')]
            
            progress_bar = st.progress(0)
            st.write("Scanning stocks...")
            
            selected_stocks = filter_stocks(tickers, progress_bar)
            
            if selected_stocks:
                st.success(f"Found {len(selected_stocks)} stocks meeting the criteria:")
                
                # Create a DataFrame for display and download
                df = pd.DataFrame(selected_stocks, columns=["Ticker", "Current RSI"])
                df = df.sort_values("Current RSI")
                
                # Display results in a table
                st.table(df)
                
                # Provide download button
                st.download_button(
                    label="Download results as CSV",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name="selected_stocks.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No stocks meet the criteria.")
        else:
            st.error("Please enter some stock tickers.")

if __name__ == "__main__":
    main()
