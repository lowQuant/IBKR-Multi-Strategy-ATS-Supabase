import curses, time
from menu_handler import  manage_settings, draw_menu
from setup import setup_database
import shared_resources

def display_logs(stdscr, width):
    with shared_resources.log_lock:
        logs = list(shared_resources.log_buffer)[-5:]  # Get the last 5 logs
    y_pos = stdscr.getmaxyx()[0] - len(logs) - 1  # Start from the bottom of the screen
    for i, log in enumerate(reversed(logs)):
        stdscr.addstr(y_pos + i, 0, log.ljust(width))

def main(stdscr):
    # Run the database setup check
    if not setup_database(stdscr):
        return  # Exit if setup needed
    
    # Set up the main window
    stdscr.nodelay(True)
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
        elif choice == ord('1'):
            stdscr.nodelay(False)
            stdscr.addstr(13, 0, "Are you sure you want to go live? (y/n)".ljust(width))
            stdscr.refresh()
            confirmation = stdscr.getch()
            if confirmation == ord('y'):
                stdscr.addstr(13, 0, "System is Live".ljust(width))
                stdscr.refresh()
            elif confirmation == ord('n'):
                stdscr.addstr(13, 0, "".ljust(width))  # Clear the quit message
            stdscr.nodelay(True)  # Make getch() non-blocking again
        elif choice == ord('2'):
            stdscr.addstr(15,2,"Reports chosen")
            stdscr.refresh()
            # ... handle 'Reports'
        elif choice == ord('q'):
            stdscr.nodelay(False)  # Make getch() blocking temporarily
            stdscr.addstr(13, 0, "Are you sure you want to quit? (y/n)".ljust(width))
            stdscr.refresh()
            confirmation = stdscr.getch()
            if confirmation == ord('y'):
                break
            elif confirmation == ord('n'):
                stdscr.addstr(13, 0, "".ljust(width))  # Clear the quit message
            stdscr.nodelay(True)  # Make getch() non-blocking again
        
        # Update the log display
        display_logs(stdscr, width)
        
        stdscr.refresh()
        time.sleep(0.1)  # To prevent high CPU usage

def start_ui():
    # Run the program
    curses.wrapper(main)

if __name__ == "__main__":
    curses.wrapper(main)