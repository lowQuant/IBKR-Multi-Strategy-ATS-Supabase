# menu_handler.py

def draw_main_menu(stdscr, width):
    stdscr.clear()
    # Draw the top bar
    stdscr.addstr(0, 0, "=" * width)

    # Title
    title = "Multi Strategy Automated Trading System by Lange Invest"
    stdscr.addstr(1, (width - len(title)) // 2, title)
    stdscr.addstr(2, 0, "=" * width)

    # Menu
    menu_title = "============== Menu =============="
    stdscr.addstr(6, (width - len(menu_title)) // 2, menu_title)

    # Menu options
    menu_options = ["Settings", "Go Live", "Reports", "Quit ATS"]
    menu_title_width = len(menu_title) - 4  # Adjust for the side bars " | "
    menu_start_x = (width - len(menu_title)) // 2  # Starting x position based on the menu title

    for i, option in enumerate(menu_options[:-1]):
        # Center each option within the width of 'menu_title'
        option_text = f"{option}".center(menu_title_width-1)
        stdscr.addstr(7 + i, menu_start_x, f"| {i}." + option_text + "|")
    # add the last menu line manually with a "q." instead of a number
    stdscr.addstr(7 + len(menu_options)-1, menu_start_x, f"| q." + f"{menu_options[-1]}".center(menu_title_width-1) + "|")

    # Bottom bar with the same length as 'menu_title' without the text
    bottom_bar = "=" * (max(len(menu_title), len(max(menu_options, key=len)) + 6))  # Adjust bottom bar length
    menu_start_x = (width - len(bottom_bar)) // 2  # Calculate starting x position
    stdscr.addstr(11, menu_start_x, bottom_bar)
    stdscr.refresh()

    choice = stdscr.getch()
    return choice


def draw_settings_menu(stdscr, width):
    stdscr.clear()
    stdscr.addstr(0, 0, "=" * width)
    title = "Multi Strategy Automated Trading System by Lange Invest"
    stdscr.addstr(1, (width - len(title)) // 2, title)
    stdscr.addstr(2, 0, "=" * width)

    # Menu title
    menu_title = "============== Settings Menu =============="
    stdscr.addstr(6, (width - len(menu_title)) // 2, menu_title)
    
    # Menu options centered within the width of 'menu_title'
    settings_options = ["General Settings", "Strategy Settings", "Add a Strategy", "Back to Main Menu"]
    menu_title_width = len(menu_title) - 4  # Adjust for the side bars " | "
    menu_start_x = (width - len(menu_title)) // 2  # Starting x position based on the menu title

    for i, option in enumerate(settings_options[:-1]):
        # Center each option within the width of 'menu_title'
        option_text = f"{option}".center(menu_title_width-1)
        stdscr.addstr(7 + i, menu_start_x, f"| {i}." + option_text + "|")
    stdscr.addstr(7 + len(settings_options)-1, menu_start_x, f"| b." + f"{settings_options[-1]}".center(menu_title_width-1) + "|")

    # Bottom bar with the same length as 'menu_title' without the text
    bottom_bar = "=" * (max(len(menu_title), len(max(settings_options, key=len)) + 6))  # Adjust bottom bar length
    menu_start_x = (width - len(bottom_bar)) // 2  # Calculate starting x position
    stdscr.addstr(11, menu_start_x, bottom_bar)
    stdscr.refresh()

    choice = stdscr.getch()
    return choice


def manage_settings(stdscr, width):
    stdscr.clear()
    # Display the settings menu
    draw_settings_menu(stdscr, width)
    
    # Wait for user input and manage the submenu logic here
    while True:
        choice = stdscr.getch()
        if choice == ord('1'):
            # Handle General Settings
            pass
        elif choice == ord('2'):
            # Handle Strategy Settings
            pass
        elif choice == ord('3'):
            # Handle Add a Strategy
            pass
        elif choice == ord('4') or choice == ord('b'):
            # Go back to the main menu
            break