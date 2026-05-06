import yfinance as yf
import pandas as pd
import webbrowser
import time

def find_breakouts(tickers):
    signals = []
    print(f"🚀 Scanning {len(tickers)} stocks...")

    for symbol in tickers:
        try:
            df = yf.download(symbol, period="100d", interval="1d", progress=False)
            if df.empty or len(df) < 40: continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Identification of the Lower High (LH)
            window = 5
            df['is_peak'] = (df['High'] == df['High'].rolling(window=window*2+1, center=True).max())
            peaks = df[df['is_peak']]['High'].tolist()

            if len(peaks) >= 2:
                last_peak = peaks[-1]
                prev_peak = peaks[-2]

                if last_peak < prev_peak:
                    current_close = df['Close'].iloc[-1]
                    yesterday_close = df['Close'].iloc[-2]

                    # Trigger Condition
                    if current_close > last_peak and yesterday_close <= last_peak:
                        print(f"✅ BREAKOUT: {symbol}!")
                        signals.append(symbol)
                        
                        # OPEN WEB PAGE LOGIC
                        # If Indian stock, open TradingView. Else, open Yahoo Finance.
                        if ".NS" in symbol:
                            clean_ticker = symbol.replace(".NS", "")
                            url = f"https://in.tradingview.com/chart/?symbol=NSE:{clean_ticker}"
                        else:
                            url = f"https://finance.yahoo.com/quote/{symbol}"
                        
                        webbrowser.open(url)
                        time.sleep(1) # Small delay to prevent browser crash

        except Exception as e:
            print(f"⚠️ Error on {symbol}: {e}")

    return signals

watchlist = ["RELIANCE.NS", "TATAMOTORS.NS", "AAPL", "NVDA", "TSLA"]
results = find_breakouts(watchlist)

if not results:
    print("😴 No breakouts found today.")