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

def connect_to_IB():
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
