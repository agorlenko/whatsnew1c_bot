import os
import psycopg2
import urllib.parse as urlparse
from telegram.ext import Updater, MessageHandler, Filters


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

print('start')
TOKEN = get_bot_token()
PORT = int(os.environ.get('PORT', '5000'))
print('bot starting')

def start(update, context):
    update.message.reply_text('Hi!')

def echo(bot, update):
    update.message.reply_text('Bot answer: ' + update.message.text)
    
updater = Updater(TOKEN)

# add handlers
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(MessageHandler(Filters.text, echo))

updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

updater.bot.setWebhook("https://whatsnew1cbot.herokuapp.com/" + TOKEN)
updater.idle()