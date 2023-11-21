import time
import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf
import quantstats as qs
from ib_insync import *
from shared_resources import ib, add_log, start_event
from . import helper_functions as hp


PARAMS = {
    1:{'name':'Monthly Trendfilter','value': 10,
       'description':"The 10M SMA Trendfilter is used as a sell signal if the price drops below."},
    2:{'name':"Structural Trendfilter",'value':50,
       'description':"""This filter is used to re-enter the market if the price is below the monthly trendfilter and was below the structural trend, but price just crossed this structural trendline from below."""},}
#     3:{'name':'Equity Weight','value':30,'description':'Weight for equity allocation'},
#     4:{'name':'Fixed Income Weight','value':90,'description':'Weight for FI allocation'},
# }

class BuyAndHold:
    def __init__(self,strategy_symbol,ib_client, symbol, exchange, currency):
        self.strategy_symbol = strategy_symbol
        self.ib_client = ib_client
        self.symbol = symbol
        self.currency = currency
        self.contract = Stock(symbol, exchange, currency)

        # check if invested - write a function that calls target_weight and checks if invested
        self.current_weight = hp.get_investment_weight(ib=ib_client,symbol=self.symbol)
        self.target_weight, self.min_weight, self.max_weight = hp.get_allocation_allowance(self.strategy_symbol)

    @staticmethod
    def check_investment_weight(any_day):
        pass

    def fetch_data(self):
        """ Fetch historical data from Interactive Brokers """
        historical_data = self.ib_client.reqHistoricalData(
            self.contract,
            endDateTime='',
            durationStr='30 Y',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1
        )
        self.df = pd.DataFrame(historical_data)
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df.set_index('date', inplace=True)

        # Calculate 50 Day MA
        self.df["50D_MA"] = self.df['close'].rolling(window=50).mean()

        # Identify and calculate 10M SMA for last trading day of each month
        self.df['month'] = self.df.index.to_period('M')
        self.month_end_df = self.df[self.df.index.day == self.df.index.map(self.last_day_of_month)].copy()
        self.month_end_df['10M_MA'] = self.month_end_df['close'].rolling(window=10).mean()
        self.month_end_df['50M_MA'] = self.month_end_df['close'].rolling(window=50).mean()

    @staticmethod
    def last_day_of_month(any_day):
        """ Return the last day of the month for a given date """
        next_month = any_day.replace(day=28) + pd.Timedelta(days=4)
        return (next_month - pd.Timedelta(days=next_month.day)).day

    def check_conditions_and_trade(self):
            """ Check the trading conditions and execute trades """
            today = dt.date.today().isoformat()
            last_data = df[df.index < today].iloc[-1]
            last_close = last_data['close']

            latest_10m_ma = self.month_end_df['10M_MA'].iloc[-1]
            latest_50m_ma = self.month_end_df['50M_MA'].iloc[-1]

            if self.invested and last_close < latest_10m_ma:
                self.execute_trade('SELL')
            elif not self.invested and last_close > latest_10m_ma:
                self.execute_trade('BUY')
            elif not self.invested and last_close > latest_50m_ma and last_close < latest_10m_ma:
                self.execute_trade('BUY')

    
    def backtest(self,yf_symbol = None,start_dt=None,end_dt=None,period=None):
        '''Backtest for the strategy. yf_symbol: Provide a Yahoo Finance Symbol if backtest should'''

        # Check if month_end_df attribute exists, if not, fetch the data
        if not hasattr(self, 'df'):
            self.fetch_data()

        if yf_symbol: # Condition for using Yahoo Finance's historical data
            self.bt_symbol = yf_symbol
            if start_dt and end_dt:
                self.bt_data = yf.download(yf_symbol, start=start_dt, end=end_dt)
                self.bt_data.rename(columns={'Adj Close': "close"}, inplace=True)
            else:
                if period:
                    self.bt_data = yf.download(yf_symbol, period=period) 
                    self.bt_data.rename(columns={'Adj Close': "close"}, inplace=True)
                else: 
                    self.bt_data = yf.download(yf_symbol)
                    self.bt_data.rename(columns={'Adj Close': "close"}, inplace=True)

            self.bt_monthly_data = self.bt_data.resample('M').last()

            #Calculate the 10M / 50M Moving Average
            self.bt_monthly_data["10M_MA"] = self.bt_monthly_data['close'].rolling(window=10).mean()
            self.bt_monthly_data["50M_MA"] = self.bt_monthly_data['close'].rolling(window=50).mean()

        else:   # Condition for using IBKR's historical data
            self.bt_symbol = self.symbol
            self.bt_data = self.df.copy()
            self.bt_monthly_data = self.month_end_df.copy()
        
        # Proceed to map monthly MAs to bt_data
        
        for i in range(len(self.bt_data)):
            current_date = self.bt_data.index[i]
            prev_month_end = current_date - pd.offsets.MonthEnd(1)
            try:
                self.bt_data.at[current_date, "10M_MA"] = self.bt_monthly_data.at[prev_month_end, "10M_MA"]
                self.bt_data.at[current_date, "50M_MA"] = self.bt_monthly_data.at[prev_month_end, "50M_MA"]
            except KeyError:
                pass

        # Drop Data before indicator is warmed-up
        self.bt_data = self.bt_data.dropna(subset=['10M_MA'])

        # Signal1 is set to 1 if the previous day's adjusted close price is greater than the previous day's 10M MA, indicating a bullish condition.
        self.bt_data['Signal1'] = np.where(self.bt_data['close'].shift(1) > self.bt_data['10M_MA'].shift(1),1,0)

        # 1. A crossover occurs where the previous day's adjusted close price is above the previous day's 50M MA and
        #    the adjusted close price from two days ago is below the 50M MA from two days ago. This indicates a bullish crossover.
        # 2. Signal1 is already set to 1, which implies that the market is bullish based on the 10M MA, so we carry over the bullish sentiment to Signal2

        self.bt_data['Signal2'] = np.where( (self.bt_data['close'].shift(1) > self.bt_data['50M_MA'].shift(1)) & 
                                            (self.bt_data['close'].shift(2) < self.bt_data['50M_MA'].shift(2)) &
                                            (self.bt_data['Signal1'] ==0)                                       |
                                            (self.bt_data['Signal1'] ==1),1, 0)

        self.bt_data['Benchmark_Returns'] = self.bt_data["close"].pct_change().fillna(0)
        self.bt_data['Strategy_Returns'] = self.bt_data['Signal2'].shift(1)*self.bt_data["close"].pct_change().fillna(0)
        return self.bt_data

    def create_bt_summary(self,yf_symbol = None,start_dt=None,end_dt=None,period=None):
        if not hasattr(self, 'bt_data'):
            self.bt_data = self.backtest(yf_symbol = None,start_dt=None,end_dt=None,period=None)

            qs.reports.html(self.bt_data['Strategy_Returns'],
                        self.bt_data['Benchmark_Returns'],
                        title=f"{yf_symbol}_{self.strategy_symbol} vs. {yf_symbol}",
                        output=f'reports/backtests/{yf_symbol}_BT.html')

        else:
            qs.reports.html(self.bt_data['Strategy_Returns'],
                            self.bt_data['Benchmark_Returns'],
                            title=f"{self.bt_symbol}_{self.strategy_symbol} vs. {self.bt_symbol}",
                            output=f'reports/backtests/{self.bt_symbol}_{self.strategy_symbol}_BT.html')































































# class Strategy:
#     def __init__(self,ib):
#         self.running = True  # This flag controls the while loop in the run method
#         self.universe = {1:{'symbol':"IUSQ",'weight':0.3},
#                          2:{'symbol':"SYB3",'weight':0.35},
#                          3:{'symbol':"IBTE",'weight':0.35}}                   
#         try:
#             # Load Cash Value from Supabase databank 
#             self.cash = 1/0
#         except:
#             # Get Cash Value from settings.ini weight * total portfolio cash
#             weight = 0.3
#             total_cash = float([line for line in ib.accountSummary() if line.tag == 'TotalCashValue'][0].value)
#             self.cash = total_cash * weight

#     def warm_up(self, contract):
#         '''Downloading historical data for each asset in the universe'''

#         def last_day_of_month(any_day):
#             # The day 28 exists in every month. 4 days later, it's always next month
#             next_month = any_day.replace(day=28) + dt.timedelta(days=4)
#             # subtracting the number of the current day brings us back one month
#             return (next_month - dt.timedelta(days=next_month.day)).day

#         df = util.df(ib.reqHistoricalData(contract,endDateTime='',durationStr='5 Y',barSizeSetting='1 day',whatToShow='TRADES',useRTH=True,formatDate=1))
#         df['date'] = pd.to_datetime(df['date'])
#         df.set_index('date', inplace=True)

#         # Add a column that identifies the last trading day of the month
#         df['last_day_of_month'] = df.index.map(last_day_of_month)
    


#     def buy_engine(self):
#         # Placeholder buy/sell engines
#         add_log("Selecting buy/sell engines...")

#         for asset in self.universe:
#             symbol = self.universe[asset]['symbol']
#             contract = Stock(symbol, 'SMART', 'EUR')

#             # is asset invested?
#             if symbol in [position.contract.symbol for position in ib.positions()]:
#                 invested = True

#                 # is the asset weight below its allocation range (0.2 - 0.3?)

#             dfd, dfm = self.warm_up(symbol)

#     def select_portfolio(self):
#         # Placeholder for portfolio selection
#         add_log("Selecting portfolio...")

#     def size_initial_position(self):
#         # Placeholder for sizing initial position
#         add_log("Sizing initial position...")

#     def execute_initial_positions(self):
#         # Placeholder for executing initial positions
#         add_log("Executing initial positions...")

#     def check_ongoing_position_size(self):
#         # Check the size of ongoing positions
#         add_log("Checking ongoing position size...")
#         positions = ib.positions()
#         for position in positions:
#             # Log the position details; implement any size checking logic as required
#             add_log(f"Position in {position.contract.symbol}: {position.position}")

#     def execute_position_adjustments(self):
#         # Placeholder for position adjustments
#         add_log("Executing position adjustments...")

#     def run(self):
#         start_event.wait()  # Wait for the start event to be set
        
#         self.select_buy_sell_engines()
#         self.select_portfolio()
#         self.size_initial_position()
#         self.execute_initial_positions()
#         while self.running:
#             self.check_ongoing_position_size()
#             self.execute_position_adjustments()
#             time.sleep(10)  # Wait for 10 seconds before checking again

def run():
    start_event.wait()
    add_log("Strategy1 Thread Started")
    while True:
        time.sleep(2)
        add_log("S1: Placing a Buy Order in AAPL")
        #strategy.running = False  # Set running to False to stop the loop


