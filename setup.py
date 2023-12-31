# setup.py

import curses
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def setup_database(stdscr):
    try:
        # Check if the settings table exists
        supabase.table("settings").select("*").execute()
        # If no error is thrown, we assume that the setup has been completed previously
        return True
    except Exception as e:
        stdscr.clear()
        stdscr.addstr("Welcome to the Automated Trading System Setup.\n")
        stdscr.addstr("It appears this is your first time running the application.\n\n")
        stdscr.addstr("""Please create the necessary tables in the sql editor of your supabase project. 
Visit 'https://supabase.com/dashboard/project/YOUR_PROJECT_ID/sql/new'
and simply copy & paste the following sql commands:\n\n""")
        
        # SQL commands for creating the tables
        stdscr.addstr("""
        CREATE TABLE settings (
            id SERIAL PRIMARY KEY,
            setting_key VARCHAR(255) NOT NULL,
            setting_value TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE strategies (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            description TEXT,
            target_weight NUMERIC,
            min_weight NUMERIC,
            max_weight NUMERIC,
            params JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        stdscr.addstr("""
        
                    PRESS ANY KEY TO CONTINUE

        """)

        stdscr.refresh()
        stdscr.getch()  # Wait for user input before showing the rest of the SQL
        stdscr.clear()

        stdscr.addstr(""" Create another table in your Supabase project:

        CREATE TABLE portfolio (
            id SERIAL PRIMARY KEY,
            strategy_id INTEGER REFERENCES strategies(id),
            symbol TEXT,
            quantity NUMERIC,
            entry_price NUMERIC,
            current_value NUMERIC,
            cash_value NUMERIC,
            date DATE,
            last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        stdscr.addstr("""
        
                    PRESS ANY KEY TO CONTINUE

        """)

        stdscr.refresh()
        stdscr.getch()  # Wait for user input before showing the rest of the SQL
        stdscr.clear()

        stdscr.addstr("""and create another one:
        
        CREATE TABLE universe (
            id SERIAL PRIMARY KEY,
            asset_type VARCHAR(255) NOT NULL,
            symbol VARCHAR(255) NOT NULL,
            name TEXT,
            sector VARCHAR(255),
            strategies TEXT[], -- array of text for possible strategies
            exchange VARCHAR(255),
            currency VARCHAR(255),
            tradingclass VARCHAR(255)
        );
        """)

        stdscr.addstr("""
        
                    PRESS ANY KEY TO CONTINUE

        """)

        stdscr.refresh()
        stdscr.getch()  # Wait for user input before showing the rest of the SQL
        stdscr.clear()

        stdscr.addstr("""

        Now add a ".env" file to the directory and create the following keys: 

        SUPABASE_URL= YOUR_PROJECT_URL
        SUPABASE_KEY= YOUR_KEY

        If you followed all instructions, you may now restart the application.
        """)
        stdscr.refresh()
        return False