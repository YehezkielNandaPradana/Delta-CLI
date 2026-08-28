import asyncio
from delta.core.events import AsyncEventBus, SystemStateEvent, LogEvent

def test_async_event_bus_pub_sub():
    async def _test():
        bus = AsyncEventBus()
        received = []

        async def handler(event: SystemStateEvent):
            received.append(event)

        bus.subscribe(SystemStateEvent, handler)
        event = SystemStateEvent(state="RUNNING", message="Engine active")
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].state == "RUNNING"
        assert received[0].message == "Engine active"

    asyncio.run(_test())

def test_async_event_bus_multiple_handlers():
    async def _test():
        bus = AsyncEventBus()
        received = []

        def sync_handler(event: LogEvent):
            received.append(f"sync:{event.message}")

        async def async_handler(event: LogEvent):
            received.append(f"async:{event.message}")

        bus.subscribe(LogEvent, sync_handler)
        bus.subscribe(LogEvent, async_handler)

        await bus.publish(LogEvent(level="INFO", message="Test log"))

        assert "sync:Test log" in received
        assert "async:Test log" in received

    asyncio.run(_test())
