import os
from typing import Any, List

from vkbottle_types.objects import UsersUserXtrCounters

from vkbottle import ABCHandler, ABCView, BaseMiddleware, CtxStorage
from vkbottle.bot import Bot, Message

bot = Bot(os.environ["token"])
dummy_db = CtxStorage()


class NoBotMiddleware(BaseMiddleware):
    async def pre(self):
        if self.event.from_id < 0:
            self.stop("Groups are not allowed to use bot")


class RegistrationMiddleware(BaseMiddleware):
    def __init__(self, event, view):
        super().__init__(event, view)
        self.cached = False

    async def pre(self):
        user = dummy_db.get(self.event.from_id)
        if user is None:
            user = (await bot.api.users.get(self.event.from_id))[0]
            dummy_db.set(self.event.from_id, user)
            self.cached = False
        else:
            self.cached = True
        self.send({"info": user})

    async def post(self):
        # Если ответ был обработан who_i_am_handler хендлером
        if who_i_am_handler in self.handlers:
            cached_str = "был" if self.cached else "не был"
            await self.event.answer(f"Ответ {cached_str} взят из кеша")


class InfoMiddleware(BaseMiddleware):
    async def post(self):
        if not self.handlers:
            self.stop("Сообщение не было обработано")

        await self.event.answer(
            "Сообщение было обработано:\n\n"
            f"View - {self.view}\n\n"
            f"Handlers - {self.handlers}"
        )


@bot.on.message(lev="кто я")
async def who_i_am_handler(message: Message, info: UsersUserXtrCounters):
    await message.answer(f"Ты - {info.first_name}")


bot.labeler.message_view.register_middleware(NoBotMiddleware)
bot.labeler.message_view.register_middleware(RegistrationMiddleware)
bot.labeler.message_view.register_middleware(InfoMiddleware)
bot.run_forever()
