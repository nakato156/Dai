from .server import Server
import asyncio
import numpy as np
from .definitions import RESET, YELLOW, GREEN

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
        
        networks_weights = list([w.weights for w in self.workers.values()])
        average_weights = []
        print([[np.array(p).shape for p in w] for w in networks_weights])
        for layer_idx in range(len(networks_weights[0])):
            layer_weights = [np.array(network[layer_idx]) for network in networks_weights]
                        
            # Verificamos que todas las redes tengan la misma forma en la capa actual
            assert all(weight.shape == layer_weights[0].shape for weight in layer_weights), f"All weights in layer {layer_idx} must have the same shape."
            
            average_layer_weights = np.mean(layer_weights, axis=0)
            
            average_weights.append(average_layer_weights)

        for worker in self.workers.values():
            await self.send_data({"weights": list(average_weights)}, worker.writer)
        
    async def _factory(self, worker:WorkerState):
        reader, writer = worker.reader, worker.writer
        writer.write(f"{self.name}".encode()) # enviamos el nombre de la fabrica
        await writer.drain()

        while True:
            data = await self.get_data(reader)
            if data:
                print(f"{YELLOW}Recibiendo data:{RESET}")
                if data["finish"]:
                    break

                elif data["state"] == 0 and not data["finish"]:
                    self.workers[worker.id].weights = data["weights"]
                    self.workers[worker.id].finished = True
                    
            if all(self.workers[w].finished for w in self.workers):
                print(f"{YELLOW}[+] updating weights....{RESET}")
                await self.update_weights()
                print(f"{YELLOW}[+] weights updated!{RESET}")
                
                for w in self.workers.values():
                    w.finished = False
                
        print(self.workers[worker.id].weights)
        print(f"{GREEN}[+]\tFinish worker {worker.id}{RESET}")
        self.workers.pop(worker.id)

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        print(f"{GREEN}Connected to {addr}{RESET}{RESET}")

        worker = self.workers[addr] = WorkerState(addr, reader, writer) #registrar worker
        asyncio.create_task(self._factory(worker)) # comunicacion con el worker

        await writer.wait_closed()

    async def start(self):
        await self.run(self._handle_client)
