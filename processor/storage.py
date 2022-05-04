import asyncio
from functools import partial
from typing import Dict, Optional, Callable, Awaitable, AnyStr, Any, Set

import aioredis
import async_timeout
from aioredis.client import PubSub

async_redis: Optional[aioredis.Redis] = None
events: Dict[str, asyncio.Event] = {}


async def init_buffer(uri: str, db: Optional[int] = None):
    global async_redis
    if uri:
        async_redis = await aioredis.from_url(uri, db=db)


async def channel_subscriber_count(channel_name: str) -> int:
    """
    Returns the number of subscribers to the user's channel and returns 0 if the channel does not exist
    :param channel_name: name of the channel (user_name)
    :return: number of channel subscribers
    """
    return next(
        ch[1] for ch in (await async_redis.pubsub_numsub(channel_name)) if ch[0] == channel_name.encode('utf_8'))


async def subscribe_channel(channel_name: str, sock_refs: Set[Callable],
                            func: Callable[[str, Set[Callable], AnyStr], Awaitable[None]]):
    """
    Subscribes to the channel through a pubsub connection and unsubscribes from channel when reader stops listening
    to channel (all the websockets got disconnected and event is set)
    :param channel_name: name of the channel (user_name)
    :param sock_refs: a set containing of the user's connected websockets references
    :param func: function that should be called when a new message is received by subscriber
    :return: None
    """
    async with async_redis.pubsub() as pubsub:
        await pubsub.subscribe(channel_name)
        await reader(pubsub, partial(func, channel_name, sock_refs))
        await pubsub.unsubscribe(channel_name)

    del events[channel_name]


async def publish_message(channel_name: str, message: Any):
    """
    Publishes the message to the specified channel
    :param channel_name: name of the channel (user_name)
    :param message: message
    :return: None
    """
    await async_redis.publish(channel_name, message)


async def reader(channel: PubSub, func: Callable[[AnyStr], Awaitable[None]]):
    """
    Subscriber listens to the channel to get the messages whenever they are published to it.
    When subscriber unsubscribes from the channel, an exception is raised and the task gets canceled
    :param channel: pubsub channel that subscriber listens to
    :param func: function that is called when a new message is received by subscriber
    :return: None
    """
    channel_name = tuple(channel.channels.keys())[0].decode()
    while not events[channel_name].is_set():
        try:
            async with async_timeout.timeout(2):
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    await func(message.get('data'))
                await asyncio.sleep(0.1)
        except asyncio.TimeoutError:
            pass
