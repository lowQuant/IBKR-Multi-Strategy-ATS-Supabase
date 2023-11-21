from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def get_allocation_allowance(strategy_symbol):
    '''Function returns allocation allowance stored in Supabase:
       - target_weight
       - min_weight
       - max_weight
    '''
    strat_data = supabase.table("strategies").select("*").execute().data
    target_weight = [s['target_weight'] for s in strat_data if s['symbol'] == strategy_symbol][0]
    min_weight = [s['min_weight'] for s in strat_data if s['symbol'] == strategy_symbol][0]
    max_weight = [s['max_weight'] for s in strat_data if s['symbol'] == strategy_symbol][0]
    return target_weight, min_weight, max_weight

def get_investment_weight(ib,symbol):
    """ Returns the investment weight in percent for the given symbol. """
    try:
        positions = ib.portfolio()

        # Sum up the investment value for all positions of the given symbol
        market_value = [pos.marketValue for pos in ib.portfolio() if pos.contract.symbol==symbol]
        market_value = market_value[0] if market_value else market_value

        if not market_value:
            return 0  # Symbol not found or has no value

        # Fetch the total equity with loan value
        equitywithloan = sum(float(entry.value) for entry in ib.accountSummary() if entry.tag == "EquityWithLoanValue")
        
        # Calculate and return the weight
        weight = (market_value / equitywithloan) * 100
        return weight

    except Exception as e:
        print(f"Error calculating investment weight: {e}")
        return None  # or handle the error as appropriate





