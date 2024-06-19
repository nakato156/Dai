import asyncio
import pickle
from .definitions import GREEN, RESET

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
    
    async def get_data(self, reader: asyncio.StreamReader) -> dict:
        buffer = b""
        while True:
            res = await reader.read(1024)
            # print("res: ", res)
            if not res:
                break
            buffer += res
            try:
                data = pickle.loads(buffer)
                return data
            except pickle.UnpicklingError:
                continue
    
    async def send_data(self, data:dict, writer: asyncio.StreamWriter):
        writer.write(pickle.dumps(data))
        await writer.drain()
        
    async def run(self, callback_client):
        server = await asyncio.start_server(callback_client, self.host, self.port)

        addr = server.sockets[0].getsockname()
        print(f"{GREEN} Serving on {addr}{RESET}")

        async with server:
            await server.serve_forever()
