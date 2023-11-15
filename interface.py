import curses
from menu_handler import  manage_settings, draw_menu
from setup import setup_database

def main(stdscr):
    # Run the database setup check
    if not setup_database(stdscr):
        return  # Exit if setup needed
    
    # Set up the main window
    stdscr.clear()
    curses.curs_set(0)  # Hide the cursor

    # Get the screen width
    height, width = stdscr.getmaxyx()

    while True:
        # Draw the main menu
        #choice = draw_main_menu(stdscr, width)
        choice = draw_menu(stdscr,width,menu_title="Main Menu",menu_options=["Settings", "Go Live", "Reports", "Quit ATS"],lastinput_key="q")

        if choice == ord('0'):
            manage_settings(stdscr, width)
            stdscr.addstr(height-1,2,f"Settings chosen {[height-1,width]}")
        elif choice == ord('1'):
            stdscr.addstr(15,2,"Live chosen")
            # ... handle 'Go Live'
        elif choice == ord('2'):
            stdscr.addstr(15,2,"Reports chosen")
            # ... handle 'Reports'


# Run the program
curses.wrapper(main)