from collections import deque
import threading

# Initialize the log buffer and lock
log_buffer = deque(maxlen=5)
log_lock = threading.Lock()

def add_log(message):
    with log_lock:
        log_buffer.append(message)
