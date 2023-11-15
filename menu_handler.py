# menu_handler.py
import curses, textwrap, importlib.util
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
            stdscr.clear()

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
                stdscr.addstr(0, 0, "=" * width)
                title = "Multi Strategy Automated Trading System by Lange Invest"
                stdscr.addstr(1, (width - len(title)) // 2, title)
                stdscr.addstr(2, 0, "=" * width)
                header = "Strategy List                 -                 Allocation"
                stdscr.addstr(5, (width // 2) - len(header) // 2, header)
                stdscr.addstr(6, (width // 2) - len(header) // 2, "-" * len(header))  # Underline the header
                line = 8

                for strat,i in zip(strategies.data,range(1,len(strategies.data)+1)):
                    name = strat['name']
                    symbol = strat['symbol']
                    target_weight = strat['target_weight']
                    display_line = f"{i}. {name} ({symbol})".ljust(40) + f"{target_weight}%".rjust(15)
                    stdscr.addstr(line, (width // 2) - len(header) // 2, display_line)
                    line += 1
        
            stdscr.addstr(line + 5, (width // 2) - len(header) // 2, "b. back")
            stdscr.refresh()

            while True:
                sub_choice = stdscr.getch()
                if sub_choice == ord('b'):
                    break
                elif sub_choice in [ord(str(i)) for i in range(1, len(strategies.data) + 1)]:
                        strategy_num = int(chr(sub_choice))
                        strategy_section = f'Strategy{strategy_num}'
                        manage_strategy(stdscr,strategy_section, width)

        # Add a Strategy Option
        elif choice == ord('2'):
            add_strategy(stdscr)
            draw_menu(stdscr,width,menu_title="Settings Menu",menu_options=["General Settings", "Strategy Settings", "Add a Strategy", "Back to Main Menu"])
        elif choice == ord('b'):
            break  # Exit settings menu

        # Refresh the screen after each action
        stdscr.refresh()
        # Include a small delay to reduce rapid looping
        curses.napms(20)

def manage_strategy(stdscr, strategy_section, width):
    needs_update = True

    # Define the width for the description
    description_width = width - 4  # Adjust the width as needed for your interface

    while True:
        if needs_update:
            stdscr.clear()
            strategy_params = load_and_initialize_strategy_params(config, settings_file, strategy=strategy_section)
            stdscr.addstr(2, 2, f"Editing Strategy: {strategy_name}")
            stdscr.addstr(4, 2, "Parameter".ljust(15) + "Name".ljust(40) + "Value".ljust(30))
            stdscr.addstr(5, 2, "-" * (15 + 40 + 30))  # Heading underline

            line = 6
            for param_id, details in strategy_params.items():
                stdscr.addstr(line, 2, f"{param_id}".ljust(15) + f"{details['name']}".ljust(40) + f"{details['value']}".ljust(30))
                line += 2
                
                # Wrap the description text to fit into the specified width
                wrapped_description = textwrap.fill(details['description'], description_width)
                description_lines = wrapped_description.split('\n')
                
                for desc_line in description_lines:
                    stdscr.addstr(line, 4, desc_line)
                    line += 1
                
                stdscr.addstr(line, 2, "-" * (15 + 40 + 30))
                line += 1

            stdscr.addstr(line + 1, 2, "Press the parameter number to edit, 'w' to change the weight, or 'b' to go back.")
            stdscr.addstr(line + 3, 2, "Press 'd' to delete this strategy.")
            stdscr.refresh()
            needs_update = False

        param_choice = stdscr.getch()
        if param_choice in [ord(str(i)) for i in range(1, len(strategy_params) + 1)]:
            param_num = int(chr(param_choice))
            param_key = f"param{param_num}"
            edit_param(stdscr, config, settings_file, strategy_section, param_key, width)
            needs_update = True  # Mark to update the display after editing

        elif param_choice == ord('w'):
            edit_weight(stdscr, config, settings_file, strategy_section, width)
            needs_update = True  # Mark to update the display after editing

        elif param_choice == ord('d'):
            delete_strategy(stdscr,config, settings_file, strategy_section)
            needs_update = True  # Mark to update the display after deletion, which will also exit the loop

        elif param_choice == ord('b'):
            break  # Exit the while loop to go back


def edit_param(stdscr, config, settings_file, strategy_section, param_key, width):
    # Clear the screen before displaying anything new
    stdscr.clear()

    # Disable nodelay to make sure getch() and getstr() block for input
    stdscr.nodelay(False)

    # Retrieve the current value and description of the parameter
    param_name = config[strategy_section][param_key + '_name']
    current_value = config[strategy_section][param_key + '_value']
    description = config[strategy_section][param_key + '_description']

    # Prompt user for new value
    stdscr.addstr(2, 2, f"Editing {param_name} (Current Value: {current_value})")
    stdscr.addstr(4, 2, description)
    stdscr.addstr(6, 2, f"Enter new value for {param_name}: ")

    # Enable echoing of input to show the user what they're typing
    curses.echo()

    # Get the new value from the user
    new_value = stdscr.getstr(6, len(f"Enter new value for {param_name}: ") + 2, 20).decode('utf-8')

    # Disable echoing of input after getting the input
    curses.noecho()

    # Validate and save the new value if needed, then update the configuration
    try:
        # Convert the new value to the appropriate type and validate it
        new_value = int(new_value)  # Example: converting to integer
        if new_value <= 0:
            raise ValueError("The value must be positive.")

        # Update the configuration
        config[strategy_section][param_key + '_value'] = str(new_value)
        with open(settings_file, 'w') as configfile:
            config.write(configfile)
        stdscr.addstr(8, 2, "Value updated successfully.")
    except ValueError as e:
        stdscr.addstr(8, 2, f"Invalid input: {e}")

    # Refresh to show the update and then wait for a key press to return
    stdscr.refresh()
    stdscr.getch()  # Now this should block since nodelay is set to False

    # If necessary, re-enable nodelay after getting the input
    stdscr.nodelay(True)

def edit_weight(stdscr, config, settings_file, strategy_section, width):
    stdscr.clear()
    stdscr.nodelay(False)
    # Prompt the user to enter a new weight
    prompt = "Enter new weight (0-100): "
    stdscr.addstr(20, 2, prompt)
    stdscr.refresh()
    curses.echo()
    new_weight = stdscr.getstr(20, 2 + len(prompt), 5).decode('utf-8')
    stdscr.nodelay(True)
    # Validate the new weight
    try:
        new_weight = int(new_weight)
        if not 0 <= new_weight <= 100:
            raise ValueError
    except ValueError:
        stdscr.addstr(22, 2, "Invalid weight. Please enter a number between 0 and 100.")
        stdscr.refresh()
        curses.napms(2000)  # Wait 2 seconds
        return

    # Update the settings.ini file with the new weight
    config.set(strategy_section, 'allocation', str(new_weight))
    with open(settings_file, 'w') as configfile:
        config.write(configfile)

def delete_strategy(stdscr, config, settings_file, strategy_section):
    stdscr.clear()
    # Confirm with the user
    stdscr.addstr(20, 2, f"Are you sure you want to delete the strategy '{config[strategy_section]['name']}'? (y/n): ")
    stdscr.refresh()
    stdscr.nodelay(False)
    confirmation = stdscr.getch()
    if confirmation in [ord('y'), ord('Y')]:
        # Remove the section from settings.ini
        config.remove_section(strategy_section)
        strategy_count = config.getint('DEFAULT', 'strategycount') - 1
        config.set('DEFAULT', 'strategycount', str(strategy_count))

        with open(settings_file, 'w') as configfile:
            config.write(configfile)

        # Call delete_strategy_from_supabase from helper_functions.py to delete supabase entry in strategies table
        delete_strategy_from_supabase(strategy_count)

        stdscr.addstr(22, 2, "Strategy deleted successfully.")
        stdscr.refresh()
        curses.napms(2000)  # Wait 2 seconds
    else:
        stdscr.addstr(22, 2, "Deletion canceled.")
        stdscr.refresh()
        curses.napms(2000)  # Wait 2 seconds
    stdscr.nodelay(True)

def load_and_initialize_strategy_params(config, settings_file, strategy):
    strategy_params = {}

    # Extract the filename from the config
    strategy_file = config.get(strategy, 'filename', fallback=None)

    if not strategy_file:
        print(f"No strategy file specified for {strategy}.")
        return strategy_params

    try:
        # Load the strategy module from the given file name
        module_name = os.path.splitext(strategy_file)[0]
        module_path = os.path.join('strategies', strategy_file)
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        strategy_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strategy_module)

        # Check if PARAMS dictionary exists and has content
        if hasattr(strategy_module, 'PARAMS') and strategy_module.PARAMS:
            default_params = strategy_module.PARAMS
        else:
            raise ImportError(f"No editable parameters found for strategy {strategy}.")

    except ImportError as e:
        # If strategy file not found or PARAMS not defined, notify the user and exit
        print(str(e))
        return strategy_params

    # Ensure the configuration file section exists
    if not config.has_section(strategy):
        config.add_section(strategy)

    # Initialize or update parameters in the config
    for param_id, details in default_params.items():
        for key in ['name', 'value', 'description']:
            config_key = f'param{param_id}_{key}'
            if not config.has_option(strategy, config_key):
                config.set(strategy, config_key, str(details[key]))

    # Save the changes to the settings file
    with open(settings_file, 'w') as configfile:
        config.write(configfile)

    # Load the parameters from the config to a dictionary
    for param_id, details in default_params.items():
        strategy_params[param_id] = {
            'name': config.get(strategy, f'param{param_id}_name'),
            'value': config.get(strategy, f'param{param_id}_value'),
            'description': config.get(strategy, f'param{param_id}_description')
        }

    return strategy_params

def delete_strategy_from_supabase(strategy_id):
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)

    # Delete the strategy from the 'strategies' table
    supabase.table("strategies").delete().eq("id", strategy_id).execute()
    print(f"Strategy with ID {strategy_id} deleted successfully from Supabase.")

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