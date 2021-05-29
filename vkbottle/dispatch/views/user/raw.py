from typing import Any, Dict, List, NamedTuple, Type

from vkbottle_types.events import BaseUserEvent, UserEventType

from vkbottle.api.abc import ABCAPI
from vkbottle.dispatch.dispenser.abc import ABCStateDispenser
from vkbottle.dispatch.handlers import ABCHandler
from vkbottle.dispatch.middlewares import BaseMiddleware, MiddlewareResponse
from vkbottle.dispatch.return_manager.user import UserMessageReturnHandler
from vkbottle.modules import logger

from ..abc import ABCView

HandlerBasement = NamedTuple(
    "HandlerBasement", [("dataclass", Type[BaseUserEvent]), ("handler", ABCHandler)]
)


class RawEventView(ABCView):
    def __init__(self):
        self.handlers: Dict[UserEventType, HandlerBasement] = {}
        self.middlewares: List["BaseMiddleware"] = []
        self.handler_return_manager = UserMessageReturnHandler()

    async def process_event(self, event: int) -> bool:
        if UserEventType(event) in self.handlers:
            return True

    async def handle_event(
        self, event: list, ctx_api: "ABCAPI", state_dispenser: "ABCStateDispenser"
    ) -> Any:
        logger.debug("Handling event ({}) with message view".format(event[0]))

        handler_basement = self.handlers[UserEventType(event[0])]
        context_variables = {}

        event_model = handler_basement.dataclass(event[1])

        if isinstance(event_model, dict):
            event_model["ctx_api"] = ctx_api
        else:
            setattr(event_model, "unprepared_ctx_api", ctx_api)

        for middleware in self.middlewares:
            response = await middleware.pre(event_model)
            if response == MiddlewareResponse(False):
                return
            elif isinstance(response, dict):
                context_variables.update(response)

        result = await handler_basement.handler.filter(event_model)
        logger.debug("Handler {} returned {}".format(handler_basement.handler, result))

        if result is False:
            return

        elif isinstance(result, dict):
            context_variables.update(result)

        handler_response = await handler_basement.handler.handle(event_model, **context_variables)

        return_handler = self.handler_return_manager.get_handler(handler_response)
        if return_handler is not None:
            await return_handler(
                self.handler_return_manager, handler_response, event_model, context_variables,
            )

        for middleware in self.middlewares:
            await middleware.post(
                event_model, self, [handler_response], [handler_basement.handler]
            )
