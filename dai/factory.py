from .server import Server
import asyncio
import numpy as np

RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"

class WorkerState:
    def __init__(self, id, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.id = id
        self.reader = reader
        self.writer = writer
        self.finished = False
        self.weights = []

class Factory(Server):
    def __init__(self, name, host, port):
        self.name = name
        super().__init__(host, port)

        # {worker_id: WorkerState(reader, wirter, finished)}
        self.workers: dict[str, WorkerState] = {}
        self.status = "idle"

    async def update_weights(self):
        print(f"{GREEN}All workers finished. Updating weights...{RESET}")
        
        combined_weights = np.mean([w.weights for w in self.workers.values()], axis=0)

        for worker in self.workers.values():
            await self.send_data({"weights": list(combined_weights)}, worker.writer)
        
    async def _factory(self, worker:WorkerState):
        reader, writer = worker.reader, worker.writer
        writer.write(f"{self.name}".encode()) #enviamos el nombre de la fabrica
        await writer.drain()

        weights = []
        while True:
            data = await self.get_data(reader)
            if data:
                if data["state"] == 0:
                    self.workers[worker.id].weights = data["weights"]
                    self.workers[worker.id].finished = True

                    
                if all(self.workers[w].finished for w in self.workers):
                    print(f"{YELLOW}[+] updating weights....{RESET}")
                    await self.update_weights()
                    print(f"{YELLOW}[+] weights updated!{RESET}")
                    
                    for w in self.workers.values():
                        w.finished = False
                    
        print(weights)
        print(f"{GREEN}[+]\tFinish worker {worker.id}{RESET}")
        return weights

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        print(f"{GREEN}Connected to {addr}{RESET}{RESET}")

        worker = self.workers[addr] = WorkerState(addr, reader, writer) #registrar worker
        await self._factory(worker) # comunicacion con el worker

        # cerrar conexion
        del self.workers[addr]
        writer.close()
        await writer.wait_closed()

    async def start(self):
        await self.run(self._handle_client)
