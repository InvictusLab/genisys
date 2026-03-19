"""Unit tests for the bus queue and message models."""

from datetime import datetime, timedelta

import pytest

from bus.queue import Broker, InboundMessage, OutboundMessage


class TestInboundMessage:
    def test_session_key_default(self):
        msg = InboundMessage(
            channel="slack",
            sender_id="user-1",
            chat_id="room-42",
            content="Hello!",
        )

        assert msg.session_key == "slack:room-42"
        assert isinstance(msg.timestamp, datetime)
        assert msg.media == []
        assert msg.metadata == {}
        assert msg.session_key_override is None

    def test_session_key_override(self):
        msg = InboundMessage(
            channel="wechat",
            sender_id="user-2",
            chat_id="group-7",
            content="Ping",
            session_key_override="custom:session",
        )

        assert msg.session_key == "custom:session"

    def test_defaults_are_not_shared(self):
        first = InboundMessage(
            channel="discord",
            sender_id="user-3",
            chat_id="thread-1",
            content="First",
        )
        second = InboundMessage(
            channel="discord",
            sender_id="user-4",
            chat_id="thread-2",
            content="Second",
        )

        first.media.append("file.png")
        first.metadata["k"] = "v"

        assert second.media == []
        assert second.metadata == {}

    def test_timestamp_default_is_recent(self):
        before = datetime.now() - timedelta(seconds=1)
        msg = InboundMessage(
            channel="matrix",
            sender_id="user-5",
            chat_id="room-9",
            content="Hey",
        )
        after = datetime.now() + timedelta(seconds=1)

        assert before <= msg.timestamp <= after


class TestOutboundMessage:
    def test_defaults(self):
        msg = OutboundMessage(
            channel="slack",
            chat_id="room-42",
            content="Hello!",
        )

        assert msg.reply_to is None
        assert msg.media == []
        assert msg.metadata == {}


class TestBroker:
    @pytest.fixture()
    def broker(self):
        return Broker()

    async def test_inbound_publish_consume_and_size(self, broker):
        msg = InboundMessage(
            channel="slack",
            sender_id="user-1",
            chat_id="room-1",
            content="Hi",
        )

        assert broker.inbound_size == 0
        await broker.publish_inbound(msg)
        assert broker.inbound_size == 1

        received = await broker.consume_inbound()
        assert received is msg
        assert broker.inbound_size == 0

    async def test_outbound_publish_consume_and_size(self, broker):
        msg = OutboundMessage(
            channel="slack",
            chat_id="room-1",
            content="Hi back",
        )

        assert broker.outbound_size == 0
        await broker.publish_outbound(msg)
        assert broker.outbound_size == 1

        received = await broker.consume_outbound()
        assert received is msg
        assert broker.outbound_size == 0

    async def test_inbound_fifo_order(self, broker):
        first = InboundMessage(
            channel="slack",
            sender_id="user-1",
            chat_id="room-1",
            content="First",
        )
        second = InboundMessage(
            channel="slack",
            sender_id="user-2",
            chat_id="room-1",
            content="Second",
        )

        await broker.publish_inbound(first)
        await broker.publish_inbound(second)

        received_first = await broker.consume_inbound()
        received_second = await broker.consume_inbound()

        assert received_first is first
        assert received_second is second
