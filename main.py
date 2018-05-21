import os
import psycopg2
import telebot
import urllib.parse as urlparse
import sys
from telebot import types

def get_bot_token():
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    try:
        conn = psycopg2.connect(dbname=dbname, user=user, host=host, password=password)
    except:
        print('I am unable to connect to the database')
        return None
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM bot_params LIMIT 1')
    row = cursor.fetchone()
    return row[0]

bot_token = get_bot_token()
bot = telebot.TeleBot(bot_token)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    keyboard = types.InlineKeyboardMarkup()
    subscribe_to_all_button = types.InlineKeyboardButton(text='Подписаться на все', callback_data='subscribe_to_all')
    keyboard.add(subscribe_to_all_button)
    bot.send_message(message.chat.id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        if call.data == 'subscribe_to_all':
            bot.send_message(call.message.chat.id, 'subscribe_to_all')

bot.polling(none_stop=True, interval=0)