from dai.factory import Factory
import asyncio

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8888

    factory = Factory("My Factory", host, port)
    asyncio.run(factory.start())