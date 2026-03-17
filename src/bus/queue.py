import asyncio
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class InboundMessage(BaseModel):
    """
    Message received from a chat channel.
    """

    channel: str
    sender_id: str
    chat_id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    media: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    session_key_override: str | None = None

    @property
    def session_key(self) -> str:
        """
        Unique key for session identification.

        Returns:
            A string that uniquely identifies the session for this message,
            used for maintaining context across messages in the same chat.
        """
        return self.session_key_override or f"{self.channel}:{self.chat_id}"


class OutboundMessage(BaseModel):
    """
    Message to send to a chat channel.
    """

    channel: str
    chat_id: str
    content: str
    reply_to: str | None = None
    media: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Broker:
    """
    Async message broker that decouples chat channels from the agent core.

    Channels push messages to the inbound queue, and the agent processes
    them and pushes responses to the outbound queue.
    """

    def __init__(self):
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()

    async def publish_inbound(self, msg: InboundMessage) -> None:
        """
        Publish a message from a channel to the agent.

        Args:
            msg: Message to be sent to agent.
        """
        await self.inbound.put(msg)

    async def consume_inbound(self) -> InboundMessage:
        """
        Consume the next inbound message (blocks until available).

        Returns:
            The next inbound message.
        """
        return await self.inbound.get()

    async def publish_outbound(self, msg: OutboundMessage) -> None:
        """
        Publish a response from the agent to channels.

        Args:
            msg: Message to be sent to channels.
        """
        await self.outbound.put(msg)

    async def consume_outbound(self) -> OutboundMessage:
        """
        Consume the next outbound message (blocks until available).

        Returns:
            The next outbound message.
        """
        return await self.outbound.get()

    @property
    def inbound_size(self) -> int:
        """
        Number of pending inbound messages.

        Returns:
            Number of pending inbound messages.
        """
        return self.inbound.qsize()

    @property
    def outbound_size(self) -> int:
        """
        Number of pending outbound messages.

        Returns:
            Number of pending outbound messages.
        """
        return self.outbound.qsize()
