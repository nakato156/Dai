from dai.ITP import ITP
from dai.worker import Worker
import typing as t
import asyncio

class ITPClient(ITP):
    async def connect(self, host: str, port: int):
        reader, writer = await asyncio.open_connection(host, port)
        self.reader = reader
        self.writer = writer

    async def close(self):
        await super().close()

    async def enviar_solicitud(self, cmd: str, data: str) -> t.Union[bytes, None]:
        return await super().enviar_solicitud(cmd, data)

    async def enviar_msg(self, data: str) -> t.Union[bytes, None]:
        return await super().enviar_msg(data)

    async def exec_cmd(self, cmd: str, data: str) -> t.Union[bytes, None]:
        return await super().exec_cmd(cmd, data)

async def main_itp():
    client = ITPClient(None, None)
    await client.connect('127.0.0.1', 8888)

    # Ejemplo de uso: enviar un mensaje
    response = await client.enviar_msg("Hola, servidor!")
    print(response.decode())

    await client.close()

async def main():
    workers = [Worker('127.0.0.1', 8888) for _ in range(3)]
    
    # Crear una lista de tareas para ejecutar en paralelo
    tasks = [worker.start() for worker in workers]
    
    # Ejecutar todas las tareas en paralelo
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())