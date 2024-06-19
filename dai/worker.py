import pickle
from collections import namedtuple
from .definitions import *
from socket import socket

WorkerInfo = namedtuple(
    "WorkerInfo",
    ["reader", "writer", "weights"],
)

class Worker:
    def __init__(self, host:str, port:int) -> None:
        self.host = host
        self.port = port
        self.sock = socket()
        self.state:int = 0 # 1 trabajando 0 detenido
        self.finish = False
    
    async def connect(self):
        self.sock.connect((self.host, self.port))
    
    async def get_data(self, sock:socket) -> dict:
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

    def work(self):
        def wrapper(func:T):
            # self.__works.append(func)
            return func
        return wrapper

    async def _work(self, target:T):
        weights = None 
        # tasks = [asyncio.create_task(work(data, weights)) for work in self.__works]

        self.state = 1
        print(f"{YELLOW}[+]\tWorker is working... for{GREEN}{RESET}")
        
        while not self.finish:
            self.state = 1
            weights = await target(WorkerInfo(self.reader, self.writer, weights))

            self.state = 0
            data = {
                "state": self.state,
                "finish": self.finish,
                "weights": list(weights),
            }

            print(f"{YELLOW}[+]\tSending weights to factory...{RESET}")
            self.writer.write(pickle.dumps(data))
            await self.writer.drain()                

            res = await self.get_data(self.reader)
            if res:
                print(f"{GREEN}[+]\tWeights received from factory{RESET}")
                print(f"{GREEN}[+]\tWeights: {res['weights']}{RESET}")
                weights = res["weights"]
                
        self.finish = True
        self.writer.write(pickle.dumps({"state": self.state, "finish": self.finish}))
    
    def start(self, target):
        self.connect()
        factory_res = (self.reader.read(1024)).decode()
        fact_name = factory_res

        print(f"{GREEN}[+]\tConnected to {fact_name}{RESET}")
        self._work(target)
