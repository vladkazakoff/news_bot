import time
import datetime
import vk_api_lib
from rss_parser import Parser
from requests import get
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import hbold, hlink
from config import tg_token, tg_channel, vk_group_ids
import difflib

# создаем объект бота, которому передаем токен, а также указываем какого типа будут
# отправляемые сообщения, создаем диспетчера, в которого передаем бота
bot = Bot(token=tg_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(commands="start")
async def start(message: types.Message):
    time_period = datetime.datetime.now().minute # за какой период учитывать новости (минуты)
    if time_period == 0: # если бота запустили ровно в 00 минут
        time_period = 60
    while True:   
        date_now = datetime.datetime.now()
        if date_now.minute == 0 and date_now.hour >= 7:
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
            time_period = 0
        else:
            time_period += 1
        time.sleep(60)


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
    posts = delete_news_doubles(posts) # избавление от дублей
    return posts[:5]


def check_count_value(obj, key, default_value): # функция проверки значений для рассчёта рейтинга
    if obj.get(key, False) == False: # проверка наличия ключа
        return default_value
    if default_value == 1 and obj[key]['count'] == 0: 
        return default_value
    return obj[key]['count']


def rate_calc(post, cnt_subs):
    view_cnt = check_count_value(post,'views', 1)
    return view_cnt / cnt_subs * 0.2 + check_count_value(post, 'likes', 0) / view_cnt * 0.5 \
           + check_count_value(post, 'comments', 0) / view_cnt * 0.8 + check_count_value(post, 'reposts', 0) / view_cnt * 1.2


def similarity(s1, s2):
    if len(s1) == 0 or len(s2) == 0:
        return 0
    normalized1 = s1.lower()
    normalized2 = s2.lower()
    matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matcher.ratio()


def delete_news_doubles(post_list):
    for i in range(len(post_list) - 1): # проверка на дубли
        for j in range(i + 1, len(post_list)):
            similarity_value = similarity(post_list[i]['text'], post_list[j]['text'])
            if similarity_value > 0.8:
                post_list[j]['is_double'] = True               
    new_post_list = [] # посты без дублей
    for post in post_list:
        if post.get("is_double", False) == False:
            new_post_list.append(post)
    return new_post_list


# запускаем бота
if __name__ == "__main__":
    executor.start_polling(dp)
