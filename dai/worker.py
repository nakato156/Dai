import pickle
from .definitions import *
from socket import socket

class Worker:
    def __init__(self, host:str, port:int, callback=None) -> None:
        self.host = host
        self.port = port
        self.sock = socket()
        self.state:int = 0 # 1 trabajando 0 detenido
        self.finish = False
        self._weights = []
        self.callback = callback(self) if callback else None

    def connect(self):
        self.sock.connect((self.host, self.port))
    
    def get_data(self, sock:socket) -> dict:
        buffer = b""
        while True:
            res = sock.recv(1024)
            if not res:
                break
            buffer += res
            try:
                data = pickle.loads(buffer)
                return data
            except pickle.UnpicklingError:
                continue

    def start(self, target, *args, **kwargs):
        self.connect()
        factory_res = (self.sock.recv(1024)).decode()
        fact_name = factory_res

        print(f"{GREEN}[+]\tConnected to {fact_name}{RESET}")
        target(*args, **kwargs, callback=self.callback.callback if self.callback else None)

