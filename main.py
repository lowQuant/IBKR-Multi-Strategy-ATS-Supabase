# main.py
import interface
# from connection_manager import establish_connection
# from logging_manager import setup_logging

def main():
    # Setup logging, connections, etc.
    # setup_logging()
    # ib = establish_connection()

    # Pass the necessary objects to the interface
    interface.start_ui()

if __name__ == "__main__":
    main()
