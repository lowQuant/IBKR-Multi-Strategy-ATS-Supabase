import curses, time
import threading

from setup import setup_database
from menu_handler import  manage_settings, draw_menu, load_strategy, get_strategies, manage_reports
from shared_resources import add_log, log_buffer, log_lock, start_event, connect_to_IB, disconnect_from_IB

def main(stdscr):
    # Run the database setup check
    if not setup_database(stdscr):
        return  # Exit if setup needed
    
    # Set up the main window
    stdscr.nodelay(True)
    stdscr.clear()
    curses.curs_set(0)  # Hide the cursor
    stdscr.refresh()

    # Get the screen width
    height, width = stdscr.getmaxyx()

     # Create a separate window for logs at the bottom of the screen
    log_win = curses.newwin(9, width, height - 9, 0)

    strategies = get_strategies()
    strategy_threads = []

    for strategy in strategies:
        strategy_module = load_strategy(strategy['filename'])
        t = threading.Thread(target=strategy_module.run)
        t.daemon = True
        t.start()
        strategy_threads.append(t)

    CONNECTED = False

    while True:
        # Draw the main menu
        if not CONNECTED:
            choice = draw_menu(stdscr,width,menu_title="Main Menu",menu_options=["Settings", "Go Live" ,"Reports", "Quit ATS"],lastinput_key="q")
        else:
            choice = draw_menu(stdscr,width,menu_title="Main Menu",menu_options=["Settings", "Disconnect","Reports", "Quit ATS"],lastinput_key="q")

        if start_event.is_set():
            log_win.erase()
            with log_lock:
                for i, log_line in enumerate(list(log_buffer)[-5:]):
                    log_win.addstr(0, 2, f"Recent Logs:".ljust(width))
                    log_win.addstr(i+1, 2, log_line[:width])
        log_win.refresh()

        # Manage Settings Menu
        if choice == ord('0'):
            manage_settings(stdscr, width)

        # Going Live & Disconnecting
        elif choice == ord('1'):
            if not CONNECTED:
                stdscr.nodelay(False)
                stdscr.addstr(13, 0, "Are you sure you want to go live? (y/n)".ljust(width))
                stdscr.refresh()
                confirmation = stdscr.getch()

                if confirmation == ord('y'):
                    stdscr.addstr(13, 0, "System is Live".ljust(width))
                    stdscr.refresh()
                    ib = connect_to_IB()
                    if ib is not None:
                        start_event.set()
                        CONNECTED = True
                elif confirmation == ord('n'):
                    stdscr.addstr(13, 0, "".ljust(width))  # Clear the quit message
                stdscr.nodelay(True)  # Make getch() non-blocking again
            
            else:
                # Disconnect from IB
                stdscr.nodelay(False)
                stdscr.addstr(13, 0, "Are you sure you want to disconnect? (y/n)".ljust(width))
                stdscr.refresh()
                confirmation = stdscr.getch()

                if confirmation == ord('y'):
                    disconnect_from_IB(ib)
                    ib = None  # Reset the IB connection object
                    CONNECTED = False
                    start_event.clear()
                elif confirmation == ord('n'):
                    stdscr.addstr(13, 0, "".ljust(width))  # Clear the message
                stdscr.nodelay(True)  # Make getch() non-blocking again

        # Showing Performance Statistics (not full yimplemented)
        elif choice == ord('2'):
            manage_reports(stdscr, width)
        
        # Quit the Application
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
        
        stdscr.refresh()
        time.sleep(0.1)  # To prevent high CPU usage

def start_ui():
    # Run the program
    curses.wrapper(main)

if __name__ == "__main__":
    curses.wrapper(main)