import asyncio
import json

import websockets


async def hello():
    async with websockets.connect("ws://0.0.0.0:8765") as websocket:
        msg = {"user_name": "37gGsvs0ghz3ittPe7d24R"}
        await websocket.send(json.dumps(msg))

        await asyncio.sleep(100)


asyncio.run(hello())
