import socket
import time

# BUG: Unbounded global cache leading to memory exhaustion
GLOBAL_CACHE = {}

class DataProcessor:
    def __init__(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = port
        self.history = []

    def fetch_and_cache(self, key, data):
        # BUG: Cache never evicts or sets TTL/LRU bound
        GLOBAL_CACHE[key] = data * 1000
        self.history.append(data)
        
    def send_log(self, message):
        # BUG: Socket connection opened without context manager or close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(message.encode())
        # Missing s.close()
