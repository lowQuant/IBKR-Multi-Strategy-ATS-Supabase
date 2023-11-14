# menu_handler.py
import curses
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def draw_menu(stdscr, width,menu_title:str,menu_options: list, lastinput_key:str="b"):
    stdscr.clear()
    # Header
    stdscr.addstr(0, 0, "=" * width)
    title = "Multi Strategy Automated Trading System by Lange Invest"
    stdscr.addstr(1, (width - len(title)) // 2, title)
    stdscr.addstr(2, 0, "=" * width)

    # Menu
    menu_title = f"============== {menu_title} =============="
    stdscr.addstr(6, (width - len(menu_title)) // 2, menu_title)
    stdscr.addstr(6, (width - len(menu_title)) // 2, menu_title)
    menu_options = menu_options
    menu_title_width = len(menu_title) - 4  # Adjust for the side bars " | "
    menu_start_x = (width - len(menu_title)) // 2  # Starting x position based on the menu title
    
    for i, option in enumerate(menu_options[:-1]):
        # Center each option within the width of 'menu_title'
        option_text = f"{option}".center(menu_title_width-1)
        stdscr.addstr(7 + i, menu_start_x, f"| {i}." + option_text + "|")

    # add the last menu line manually with the lastinput_key variable (default: b for back) instead of a number
    stdscr.addstr(7 + len(menu_options)-1, menu_start_x, f"| {lastinput_key}." + f"{menu_options[-1]}".center(menu_title_width-1) + "|")
    
    # Bottom bar with the same length as 'menu_title' without the text
    bottom_bar = "=" * (max(len(menu_title), len(max(menu_options, key=len)) + 6))  # Adjust bottom bar length
    menu_start_x = (width - len(bottom_bar)) // 2  # Calculate starting x position
    stdscr.addstr(7+ len(menu_options), menu_start_x, bottom_bar)
    stdscr.refresh()

    choice = stdscr.getch()
    return choice

def draw_main_menu(stdscr, width):
    draw_menu(stdscr,width,menu_title="Settings Menu",
    menu_options=[
    "General Settings", 
    "Strategy Settings", 
    "Add a Strategy", 
    "Back to Main Menu"])

def prompt_user(win, prompt, y, input_x, visible_length, total_length, width):
    # Display the prompt at a fixed position
    win.addstr(y, 2, prompt)  # 2 to offset from the window border
    win.refresh()

    curses.echo()
    input_str = ''
    while not input_str:
        win.move(y, input_x)  # Move cursor to the input position
        win.clrtoeol()  # Clear the line where the input is to be entered
        input_str = win.getstr().decode().strip()  # Get input from the user
        if not input_str:
            # If input is empty, prompt the user again
            win.addstr(y + 1, 2, "Input cannot be empty. Please enter a value.")
            win.refresh()
            curses.napms(1000)  # Wait a second before allowing to enter again
            win.move(y + 1, 2)  # Move cursor away from the error message
            win.clrtoeol()  # Clear the error message

    curses.noecho()
    return input_str


def add_strategy(stdscr):
    height, width = stdscr.getmaxyx()
    curses.echo()

    # Create a new window for the form and display a border
    win = curses.newwin(height, width, 0, 0)
    win.box()

    # Fixed positions for the input cursor
    input_x = max(width // 4, 30)  # Adjust the x value as needed for layout

    # Input fields
    strategy_name = prompt_user(win, "Enter Strategy Name: ", 5, input_x, visible_length=60,total_length=100, width=width)
    strategy_abbreviation = prompt_user(win, "Enter Symbol for Strategy: ", 7, input_x, visible_length=60, total_length=20, width=width)
    file_name = prompt_user(win, "Enter Python File Name: ", 9, input_x, visible_length=60, total_length=20, width=width)
    allocation = prompt_user(win, "Enter Allocation (0-100): ", 11, input_x, visible_length=60, total_length=10, width=width)

    # Validation
    curses.noecho()
    curses.curs_set(0)  # Hide cursor after inputs

    try:
        if allocation == '':  # Check if allocation input is empty
            raise ValueError("Allocation input cannot be empty.")
        allocation_int = int(allocation)
        if not 0 <= allocation_int <= 100:
            win.addstr(16, 2, "Allocation must be between 0 and 100.".ljust(width))
            win.refresh()
            stdscr.nodelay(False) 
            stdscr.getch()
            stdscr.nodelay(True) 
            raise ValueError("Allocation must be between 0 and 100.")
    except ValueError as e:
        win.addstr(22, 2, f"Error: {e}. Press any key to continue...".ljust(width))
        win.refresh()
        stdscr.nodelay(False) 
        stdscr.getch()
        stdscr.nodelay(True) 
        return  # Exit the function if validation fails

    # Confirmation before saving
    win.addstr(15, 2, "Save this information? (y/n): ")
    win.refresh()
    confirmation = win.getch()
    if confirmation in [ord('n'), ord('N')]:
        win.addstr(16, 2, "Operation cancelled. Press any key to continue...")
        win.refresh()
        stdscr.nodelay(False) 
        stdscr.getch()
        stdscr.nodelay(True) 
        return  # Return without saving
    
    if confirmation in [ord('y'), ord('Y')]:
        # Assuming validation passed and confirmed, update the database

        strategy_details = {
            'name': strategy_name,
            'symbol': strategy_abbreviation,
            'description': "",
            'filename': file_name,
            'target_weight':float(allocation),
            'min_weight':float(allocation)*0.8,
            'max_weight':float(allocation)*1.2,
            }
        try:
            res = supabase.table("strategies").select("symbol").eq("symbol", strategy_abbreviation).execute()
            if not res.data: # if strategy not already in supabase, add it
                supabase.table("strategies").insert(strategy_details).execute()
            else:
                supabase.table("strategies").update(strategy_details).eq("symbol", strategy_abbreviation).execute()
        except:
            pass
        
        # Success message
        success_msg = f"{strategy_name} strategy added successfully! Press any key to continue..."
        success_msg_x = (width - len(success_msg)) // 2  # Center the message
        win.addstr(17, success_msg_x, success_msg)
        win.refresh()

        stdscr.nodelay(False) 
        stdscr.getch()  # Wait for user input before continuing
        stdscr.nodelay(True)
        win.clear() # Clear the window and return to the main screen
        win.refresh()


def manage_settings(stdscr, width):
    # Display the settings menu
    draw_menu(stdscr,width,menu_title="Settings Menu",menu_options=["General Settings", "Strategy Settings", "Add a Strategy", "Back to Main Menu"])
    while True:
        choice = stdscr.getch()

        # General Settings Option
        if choice == ord('0'):
            draw_menu(stdscr,width,"General Settings",menu_options=["Change Port for IBKR Connection", "Back to Settings Menu"])
            while True:  # Begin nested loop for the General Settings submenu
                sub_choice = stdscr.getch()
                if sub_choice == ord('0'):
                    change_port(stdscr,width)
                    draw_menu(stdscr,width,menu_title="Settings Menu",menu_options=["General Settings", "Strategy Settings", "Add a Strategy", "Back to Main Menu"])
                    break
                elif sub_choice == ord('b'):
                    break

        # Strategy Settings Option
        elif choice == ord('1'):
            # Fetch strategies from Supabase
            strategies = supabase.table("strategies").select("*").execute()
            
            # if no strategy in Supabase
            if len(strategies.data) == 0:
                draw_menu(stdscr,width,"Strategies",["Add a Strategy","Back to Settings"])
                while True:  # Begin nested loop for the General Settings submenu
                    sub_choice = stdscr.getch()
                    if sub_choice == ord('0'):
                        add_strategy(stdscr)
                        draw_menu(stdscr,width,"Strategies",["Add a Strategy","Back to Settings"])
                        break
                    elif sub_choice == ord('b'):
                        break
            else:
                # Display strategies and allow the user to manage them
                pass
        
        # Add a Strategy Option
        elif choice == ord('2'):
            # Call a function to add a new strategy
            # This function would interact with Supabase to insert a new strategy
            pass
        
        # Back Option
        elif choice == ord('b'):
            break  # Exit settings menu

        # Refresh the screen after each action
        stdscr.refresh()
        # Include a small delay to reduce rapid looping
        curses.napms(20)

def draw_general_settings(stdscr, width):
    stdscr.clear()
    stdscr.addstr(0, 0, "=" * width)
    title = "Multi Strategy Automated Trading System by Lange Invest"
    stdscr.addstr(1, (width - len(title)) // 2, title)
    stdscr.addstr(2, 0, "=" * width)

    # Menu title
    menu_title = "============== General Settings =============="
    stdscr.addstr(6, (width - len(menu_title)) // 2, menu_title)
    
    # Menu options centered within the width of 'menu_title'
    settings_options = ["Change Port for IBKR Connection", "Back to Settings Menu"]
    menu_title_width = len(menu_title) - 4  # Adjust for the side bars " | "
    menu_start_x = (width - len(menu_title)) // 2  # Starting x position based on the menu title

    for i, option in enumerate(settings_options[:-1]):
        # Center each option within the width of 'menu_title'
        option_text = f"{option}".center(menu_title_width-1)
        stdscr.addstr(7 + i, menu_start_x, f"| {i+1}." + option_text + "|")
    stdscr.addstr(7 + len(settings_options)-1, menu_start_x, f"| b." + f"{settings_options[-1]}".center(menu_title_width-1) + "|")

    # Bottom bar with the same length as 'menu_title' without the text
    bottom_bar = "=" * (max(len(menu_title), len(max(settings_options, key=len)) + 6))  # Adjust bottom bar length
    menu_start_x = (width - len(bottom_bar)) // 2  # Calculate starting x position
    stdscr.addstr(9, menu_start_x, bottom_bar)
    stdscr.refresh()

    choice = stdscr.getch()
    return choice

def change_port(stdscr, width):
    
    curses.echo()
    win = curses.newwin(10, 50, 5, (width - 50) // 2)  # Adjust size and position as needed
    win.box()
    win.addstr(1, 2, """Enter new port (4 digits):""")
    win.refresh()
    curses.curs_set(1)  # Show cursor
    while True:
        try:
            win.move(1, 28)  # Move cursor to the right of the prompt
            new_port_str = win.getstr().decode().strip()
            if len(new_port_str) == 4 and new_port_str.isdigit():
                new_port = int(new_port_str)
                try:
                    res = supabase.table("settings").select("setting_value").eq('setting_key', 'port').execute()
                    if res.data:
                        update_result = supabase.table("settings").update({"setting_value": new_port}).eq('setting_key', 'port').execute()
                except:
                    supabase.table("settings").insert({"setting_key": "port", "setting_value": new_port}).execute()

                win.addstr(3, 2, "Port changed successfully.", curses.A_BOLD)
                win.refresh()
                break
            else:
                raise ValueError
        except ValueError:
            win.move(2, 2)
            win.clrtoeol()
            win.addstr(2, 2, "Invalid port. Try again.", curses.A_BOLD)
            win.refresh()

    curses.curs_set(0)  # Hide cursor
    curses.noecho()
    win.getch()  # Wait for user input before closing the window
    win.clear()
    win.refresh()

