from typing import Tuple
import asyncio
import json
from random import randint, random
import numpy as np

RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"

class Worker:
    def __init__(self, host, port) -> None:
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None
        self.state:str = "idle"
        self.finish = False
    
    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
    
    async def get_data(self, reader: asyncio.StreamReader) -> dict:
        buffer = b""
        while True:
            res = await reader.read(1024)
            if not res:
                break
            buffer += res
            try:
                data = json.loads(buffer.decode())
                return data
            except json.JSONDecodeError:
                continue

    async def work(self):
        weights = np.random.rand(10)  # Genera pesos aleatorios
        for i in range(10):    
            seg = randint(5, 10)
            print(f"{YELLOW}[+]\tWorker is working step {i+1}... for{GREEN} {seg}s{RESET}")
            await asyncio.sleep(seg)  # Simula una operación asíncrona
            
            self.finish = True
            self.state = 0
            res = {
                "state": self.state,
                "weights": list(weights),
            }
            print(f"{YELLOW}[+]\tSending weights to factory...{RESET}")
            self.writer.write(json.dumps(res).encode())
            await self.writer.drain()  # Asegura que los datos se envíen
            
            self.finish = False

            res = await self.get_data(self.reader)
            if res:
                print(f"{GREEN}[+]\tWeights received from factory{RESET}")
                print(f"{GREEN}[+]\tWeights: {res['weights']}{RESET}")
                weights += res["weights"]
    
    async def start(self):
        await self.connect()
        factory_res = (await self.reader.read(1024)).decode()
        fact_name = factory_res

        print(f"{GREEN}[+]\tConnected to {fact_name}{RESET}")        
        await self.work()
