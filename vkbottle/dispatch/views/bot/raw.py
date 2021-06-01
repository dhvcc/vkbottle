from typing import Callable, Dict, NamedTuple

from vkbottle_types.events import GroupEventType

from vkbottle.dispatch.handlers import ABCHandler
from vkbottle.dispatch.return_manager.bot import BotMessageReturnHandler
from vkbottle.dispatch.views.abc import ABCRawEventView

HandlerBasement = NamedTuple("HandlerBasement", [("dataclass", Callable), ("handler", ABCHandler)])


class RawEventView(ABCRawEventView):
    def __init__(self):
        super().__init__()
        self.handlers: Dict[GroupEventType, HandlerBasement] = {}
        self.handler_return_manager = BotMessageReturnHandler()

    def get_handler_basement(self, event):
        return self.handlers[GroupEventType(self.get_event_type(event))]

    def get_event_model(self, handler_basement, event):
        return handler_basement.dataclass(**event)

    @staticmethod
    def get_event_type(event: dict) -> str:
        return event["type"]

    async def process_event(self, event: dict) -> bool:
        return GroupEventType(self.get_event_type(event)) in self.handlers
