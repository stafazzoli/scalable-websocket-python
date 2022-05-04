import asyncio
import logging
import weakref
from contextvars import ContextVar
from typing import Dict, Set, Callable, Optional

import rapidjson

from processor.inapp import send_socket_message
from processor.storage import subscribe_channel, events

connected_sockets: Dict[str, Set[Callable]] = {}

current_user: ContextVar[str] = ContextVar('Current User')


async def websocket_handler(ws):
    ref = weakref.ref(ws)
    try:
        logging.debug('Socket connected.')

        async for message in ws:

            if message == 'ping':
                await ws.send('pong')
                continue

            data = rapidjson.loads(message)
            user_name: Optional[str] = data.get('user_name')
            if user_name:
                key = user_name.lower()

                logging.info('%s connected from device.', user_name)

                if key not in connected_sockets:
                    connected_sockets[key] = set()
                    events[key] = asyncio.Event()
                    asyncio.create_task(subscribe_channel(key, connected_sockets[key], send_socket_message))

                if key in connected_sockets and ref not in connected_sockets[key]:
                    connected_sockets[key].add(ref)
                    current_user.set(user_name)

                logging.info('Number of connections for %s: %d', key, len(connected_sockets[key]))
            else:
                user_name = current_user.get()

    except Exception as e:
        logging.debug("Exception: %s", e)
    finally:
        logging.debug('Socket disconnected.')

        if user_name := current_user.get(None):
            logging.warning('Socket disconnected for %s.', user_name)

            key = user_name.lower()

            if key in connected_sockets:
                connected_sockets[key].remove(ref)
                logging.info('Number of connections for %s: %d', key, len(connected_sockets[key]))

                if not connected_sockets[key]:
                    del connected_sockets[key]
                    events[key].set()
