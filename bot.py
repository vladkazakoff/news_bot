import time
import datetime
import vk_api_lib
from rss_parser import Parser
from requests import get
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import hbold, hlink
from config import tg_token, tg_channel, vk_group_ids

# создаем объект бота, которому передаем токен, а также указываем какого типа будут
# отправляемые сообщения, создаем диспетчера, в которого передаем бота
bot = Bot(token=tg_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(commands="start")
async def start(message: types.Message):
    while True:   

        hour_now = (datetime.datetime.utcnow()).hour + 5 # Пермское время: UTC + 5:00 (часы)
        break_length = 7 # длительность ночного перерыва (часы)
        time_period = 60 # за какой период учитывать новости (минуты)
        if hour_now >= 7 and hour_now < 8: # после ночного перерыва (07:00 - 08:00) учесть новости за это время
            time_period = 60 * break_length

        vk_lib = vk_api_lib.VkApiLib()
        top_posts = top_post_calculator(vk_collector(vk_lib), time_period)

        i = 0
        message = ''
        media = []
        for post in top_posts:
            # for attach in post['attachments']:
            #    if attach['type'] == 'photo':
            #        media.append(attach['photo']['sizes'][4]['url'])
            link = 'Источник: https://vk.com/wall' + str(post['owner_id']) + '_' + str(post['id'])
            text = post['text'][0:150].replace('\n', '') + '...'
            i += 1
            message = '<b>' + text + '</b>\n' + link + '\n\n'
            await bot.send_message(tg_channel, message)
        
        if hour_now >= 0 and hour_now < 1: # в период с 00:00 до 01:00 нужно приостановить работу на ночь
            time.sleep(3600 * break_length)
        else:
            time.sleep(3600)


def vk_collector(vk_lib):
    info = []

    for group_id in vk_group_ids:
        posts = vk_lib.get_wall_posts(count=20, group_id=-group_id)
        group = vk_lib.get_group_info(group_id=group_id)
        summary = {'group': group[0], 'posts': posts['items']}
        info.append(summary)
    return info


def top_post_calculator(vk_collection, t_period):
    posts = []
    for group in vk_collection:
        subscribers = group['group']['members_count']
        for post in group['posts']:
            if post['date'] > time.mktime(datetime.datetime.now().timetuple()) - t_period * 60:
                post['rate'] = rate_calc(post, subscribers)
                post['source_domain'] = group['group']['screen_name']
                post['source_name'] = group['group']['name']
                posts.append(post)
    posts = sorted(posts, key=lambda d: d['rate'], reverse = True)
    return posts[:5]

def rate_calc(post, cnt_subs):
    view_cnt = post['views']['count']
    return view_cnt / cnt_subs * 0.2 + post['likes']['count'] / view_cnt * 0.5 \
           + post['comments']['count'] / view_cnt * 0.8 + post['reposts']['count'] / view_cnt * 1.2


# запускаем бота
if __name__ == "__main__":
    executor.start_polling(dp)
