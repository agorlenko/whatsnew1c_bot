import os
import psycopg2
import telebot
import urllib.parse as urlparse
import sys

def get_bot_token():
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    #try:
    conn = psycopg2.connect(dbname=dbname, user=user, host=host, password=password)
    #except:
    #    print('I am unable to connect to the database')
    #    return None
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM bot_params LIMIT 1')
    row = cursor.fetchone()
    return row[0]

print('Hi!!!', file=sys.stderr)
bot = telebot.TeleBot(get_bot_token())

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == 'Hi':
        bot.send_message(message.from_user.id, 'Hello! I am WhatsNew1C_bot. How can i help you?')
    elif message.text == 'How are you?' or message.text == 'How are u?':
        bot.send_message(message.from_user.id, 'I am fine, thanks. And you?')
    else:
        bot.send_message(message.from_user.id, 'Sorry, i dont understand you.')

#telebot.apihelper.proxy = {'https':'socks5://138.68.59.157:1210'}

bot.polling(none_stop=True, interval=0)