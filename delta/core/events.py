import inspect
from typing import Type, Callable, Dict, List, Any
from pydantic import BaseModel

class SystemStateEvent(BaseModel):
    state: str
    message: str

class AgentStepEvent(BaseModel):
    step: int
    thought: str
    action: str

class ToolExecutionEvent(BaseModel):
    tool_name: str
    args: dict
    output: str

class FindingDiscoveredEvent(BaseModel):
    title: str
    severity: str
    target: str

class LogEvent(BaseModel):
    level: str
    message: str

class AsyncEventBus:
    def __init__(self):
        self._subscribers: Dict[Type[BaseModel], List[Callable[[Any], Any]]] = {}

    def subscribe(self, event_type: Type[BaseModel], handler: Callable[[Any], Any]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event: BaseModel):
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                if inspect.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
