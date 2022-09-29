import time

from rss_parser import Parser
from requests import get
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import hbold, hlink
from config import tg_token, tg_channel;

# создаем объект бота, которому передаем токен, а также указываем какого типа будут
# отправляемые сообщения, создаем диспетчера, в которого передаем бота
bot = Bot(token=tg_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


# указываем обработку диспетчером комманды start
# создаем функцию в которой будем отправлять сообщения
# для этого явно указываем на тип сообщений
@dp.message_handler(commands="start")
async def start(message: types.Message):
    habr_title = []

    # запускаем бесконечный цикл, в котором будем проверять наличие новостей
    while True:
        if len(habr_title) >= 20:
            habr_title = []
        rss_url = "https://habr.com/ru/rss/news/?fl=ru"
        xml = get(rss_url)

        parser = Parser(xml=xml.content, limit=3)
        feed = parser.parse()

        # пробегаемся по каждой новости в цикле
        for item in reversed(feed.feed):
            # проверяем есть ли заголовок новости в списке
            if not item.title in habr_title:
                habr_title.append(item.title)
                # отправляем сообщение
                # await message.answer(f'{hbold(item.publish_date)}\n\n{hlink(item.title, item.link)}\n\n')
                await bot.send_message(tg_channel, f'{hbold(item.publish_date)}\n\n{hlink(item.title, item.link)}\n\n')
        time.sleep(1800)


# запускаем бота
if __name__ == "__main__":
    executor.start_polling(dp)