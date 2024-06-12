from typing import Tuple
import asyncio
import json

RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
    
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
    
    async def send_data(self, data:dict, writer: asyncio.StreamWriter):
        writer.write(json.dumps(data).encode())
        await writer.drain()
        
    async def run(self, callback_client):
        server = await asyncio.start_server(callback_client, self.host, self.port)

        addr = server.sockets[0].getsockname()
        print(f"{GREEN} Serving on {addr}{RESET}")

        async with server:
            await server.serve_forever()
