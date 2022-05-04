import asyncio
import logging.config

import websockets

import configs
from handler import websocket_handler
from processor.storage import init_buffer

loop = asyncio.get_event_loop()


async def init_hub():
    await init_buffer(configs.STORAGE)


async def bootstrap():
    await init_hub()
    await websockets.serve(websocket_handler, configs.LISTEN_HOST, configs.LISTEN_PORT)


if __name__ == '__main__':
    logging.config.fileConfig(configs.LOGGING)
    loop.run_until_complete(bootstrap())
    logging.info('Notification worker got up & running right now!')
    loop.run_forever()
