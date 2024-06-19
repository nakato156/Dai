from dai.factory import Factory
import asyncio

if __name__ == '__main__':
    host = '172.21.32.1'
    port = 8888

    factory = Factory("My Factory", host, port)
    asyncio.run(factory.start())