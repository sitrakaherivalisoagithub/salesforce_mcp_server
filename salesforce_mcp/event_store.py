import logging
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import uuid4

from mcp.server.streamable_http import (
    EventCallback,
    EventId,
    EventMessage,
    EventStore,
    StreamId,
)
from mcp.types import JSONRPCMessage

logger = logging.getLogger(__name__)

@dataclass
class EventEntry:
    """Data model for a stored event."""
    event_id: EventId
    stream_id: StreamId
    message: JSONRPCMessage

class InMemoryEventStore(EventStore):
    """A simple in-memory implementation for resumability."""
    def __init__(self, max_events_per_stream: int = 100):
        self.max_events_per_stream = max_events_per_stream
        self.streams: dict[StreamId, deque[EventEntry]] = {}
        self.event_index: dict[EventId, EventEntry] = {}
        logger.info(f"InMemoryEventStore initialized with {max_events_per_stream} max events per stream.")

    async def store_event(self, stream_id: StreamId, message: JSONRPCMessage) -> EventId:
        """Stores a new event message."""
        event_id = str(uuid4())
        event_entry = EventEntry(event_id=event_id, stream_id=stream_id, message=message)
        
        if stream_id not in self.streams:
            self.streams[stream_id] = deque(maxlen=self.max_events_per_stream)
        
        if len(self.streams[stream_id]) == self.max_events_per_stream:
            # If the deque is full, the oldest event is automatically removed.
            # We also need to remove it from the lookup index.
            oldest_event = self.streams[stream_id][0] 
            self.event_index.pop(oldest_event.event_id, None)
            
        self.streams[stream_id].append(event_entry)
        self.event_index[event_id] = event_entry
        return event_id

    async def replay_events_after(self, last_event_id: EventId, send_callback: EventCallback) -> StreamId | None:
        """Replays events from a stream after a given event ID."""
        if last_event_id not in self.event_index:
            logger.warning(f"Event ID {last_event_id} not found for replay.")
            return None
        
        last_event = self.event_index[last_event_id]
        stream_id = last_event.stream_id
        stream_events = self.streams.get(stream_id, deque())
        
        found_last = False
        replayed_count = 0
        for event in stream_events:
            if found_last:
                await send_callback(EventMessage(event.message, event.event_id))
                replayed_count += 1
            elif event.event_id == last_event_id:
                found_last = True
        
        logger.debug(f"Replayed {replayed_count} events for stream {stream_id}")
        return stream_id
