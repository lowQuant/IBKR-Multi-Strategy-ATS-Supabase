from collections import deque
import threading, time, supabase
from ib_insync import *

util.startLoop() # comment out for live environment

# Initialize the log buffer and lock
log_buffer = deque(maxlen=5)
log_lock = threading.Lock()
start_event = threading.Event()

def add_log(message):
    with log_lock:
        log_buffer.append(f"{time.ctime()}: {message}")

# Declare ib as a global variable
ib = None

def connect_to_IB():
    global ib  # Use the global keyword to modify the global instance
    ib = IB()
    try:
        port = supabase.table("settings").select("setting_value").eq('setting_key', 'port').execute().data[0]['setting_value']
    except:
        port = 7497

    try:
        ib.connect('127.0.0.1', port, clientId=0)
        add_log('IB Connection established with ClientId=0')
        return ib
    except:
        try:
            ib.connect('127.0.0.1', port, clientId=1)
            add_log('IB Connection established with clientId=1')
            return ib
        except:
            add_log('Connection failed. Start TWS or TWS Gateway and try again!')
            return None

def disconnect_from_IB(ib):
    if ib.isConnected():
        ib.disconnect()
        add_log("Disconnected from Interactive Brokers.")