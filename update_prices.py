from supabase import create_client
from dotenv import load_dotenv
import os, time
import matplotlib as plt
from ib_insync import *
import financedatabase as fd
import talib

import pandas as pd
import numpy as np
import datetime as dt

import logging

# Set the logging level to WARNING to suppress INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)


load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=0)


def get__last_trading_day():
    today = dt.datetime.today()
    # If it's Saturday (6) or Sunday (7), return last Friday's date
    if today.weekday() == 5:  # Saturday
        trading_day = today - dt.timedelta(days=1)
    elif today.weekday() == 6:  # Sunday
        trading_day = today - dt.timedelta(days=2)
    else:  # Weekday
        trading_day = today

    return trading_day


# Initialize the Equities database
equities = fd.Equities()
# Find all US stocks
us_stocks = equities.select(country="United States", exclude_exchanges=False)
# Filter to domestic stocks & US Exchange Listings only with active ISINs
us_stocks = us_stocks[(us_stocks['currency']=='USD') & (~us_stocks.index.str.contains('\\.'))].dropna(subset=['isin']).dropna(subset=['cusip'])

symbols = us_stocks.index.unique()
contracts = [Stock(con,'SMART','USD') for con in symbols]
contracts = ib.qualifyContracts(*contracts)

print(dt.datetime.now())
for con in contracts[:]:
    
    try:
        # Initialize your data collection
        all_insert_data = []
        bars = ib.reqHistoricalData(contract=con,endDateTime='',durationStr='1 Y',barSizeSetting='1 day',whatToShow='ADJUSTED_LAST',useRTH=True)
        
        if [bar.date for bar in bars[-1:]] == [get__last_trading_day().date()]: # checks if stock is actively traded
            # Convert to DataFrame
            df = util.df(bars)
            df = df.drop(columns=['average','barCount'])
            df['symbol'] = con.symbol

            # Ensure the 'date' column is in datetime format and set as the DataFrame index
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            # Calculate Moving Averages and other technical indicators
            df['50D_MA'] = talib.SMA(df['close'], timeperiod=50)
            df['200D_MA'] = talib.SMA(df['close'], timeperiod=200)
            #df['10M_MA'] = talib.SMA(df['close'], timeperiod=10*30)  # Approximating 30 days per month
            df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)  # Using 14-day ATR by convention
            df['52W_High'] = df['close'].rolling(window=52*5, min_periods=1).max()  # Assuming 5 trading days in a week
            
            # Reset index to turn the 'date' back into a column and format it as a string
            df.reset_index(inplace=True)
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')

            # Replace NaN values with None before converting to a dictionary
            df = df.replace({np.nan: None})

            # Prepare data for insert
            all_insert_data = df.to_dict(orient='records')

            # Perform bulk insert
            response = supabase.table('prices').upsert(all_insert_data).execute()
            print(f"Updated: {con.symbol}. {symbols.tolist().index(con.symbol) + 1} out of {len(symbols)} symbols updated.")

    except Exception as e:
        print(f"Error: {e} occurred while updating {con.symbol}")

print(dt.datetime.now())
           
           
    #         # Get all existing data for this symbol
    #         existing_data = supabase.table('prices').select('date').eq('symbol', con.symbol).execute().data
    #         existing_dates = {data['date'] for data in existing_data} if existing_data else set()
            
    #         values = util.tree(bars)
    #         symbol = con.symbol
    #         for bar in values:
    #             bar_date = bar['BarData']['date']
    #             if bar_date not in existing_dates:
    #                 insert_data = {
    #                     'date': bar_date,
    #                     'open': bar['BarData']['open'],
    #                     'high': bar['BarData']['high'],
    #                     'low': bar['BarData']['low'],
    #                     'close': bar['BarData']['close'],
    #                     'volume': bar['BarData']['volume'],
    #                     'symbol': symbol
    #                 }
    #                 all_insert_data.append(insert_data)
            
    #         # Perform bulk insert
    #         if all_insert_data:
    #             response = supabase.table('prices').insert(all_insert_data).execute()
    #             print(f"Updated:   {symbol}.  {symbols.to_list().index(symbol) + 1} out of {len(symbols)} symbols updated.")

    # except Exception as e:
    #     print(f"Error: {e} occurred while updating {con.symbol}")


print(dt.datetime.now())