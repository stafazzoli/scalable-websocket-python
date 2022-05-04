import json
import logging
from typing import AnyStr, Set, Callable

from processor.storage import publish_message, channel_subscriber_count


async def publish_socket_message(event: dict,
                                 user_name: str) -> bool:
    key = user_name.lower()
    event_sent: bool = False

    if await channel_subscriber_count(key):

        event.message = f'Websocket test for {user_name}'
        data = json.dumps(event)

        await publish_message(key, data)
        event_sent = True

        logging.info("Published event %s to channel %s.", event.event_type, key)
    else:
        logging.warning('Could not inform %s via socket. Keep the event.', key)

    return event_sent


async def send_socket_message(key: str, sock_refs: Set[Callable], message: AnyStr):
    try:
        for ref in sock_refs:
            await ref().send(message.decode('utf_8'))

        logging.debug("%s with %d connected websockets got informed.", key, len(sock_refs))
    except Exception as e:
        logging.error("Failed to inform %s via socket. Error: %s", key, e)
