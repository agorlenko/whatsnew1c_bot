import os
import psycopg2
import urllib.parse as urlparse
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters


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

def get_db_conn_params():
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
    return {'dbname': url.path[1:], 'user': url.username, 'password': url.password, 'host': url.hostname}

print('start')
TOKEN = os.environ['BOT_TOKEN']
PORT = int(os.environ.get('PORT', '5000'))
print('bot starting')

keyboard = [['Подписаться на все', 'Отменить подписку']]    
markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)    

def start(bot, update):
    #keyboard = [[InlineKeyboardButton("Option 1", callback_data='1'), InlineKeyboardButton("Option 2", callback_data='2')], [InlineKeyboardButton("Option 3", callback_data='3')]]
    update.message.reply_text('Hi!', reply_markup=markup)

def echo(bot, update):
    update.message.reply_text('Bot answer: ' + update.message.text)

def handler(bot, update):
    if update.message.text == 'Подписаться на все':
        subscribe_to_all(update)
    elif update.message.text == 'Отменить подписку':
        unsubscribe_from_all(update)
    else:
        update.message.reply_text('Неизвестное действие')

def subscribe_to_all(update):
    db_conn_params = get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT id, subscribed_to_all FROM subscribers WHERE id = %s', (update.message.chat.id,))
            row = curs.fetchone()
            if not row:
                curs.execute('INSERT INTO subscribers (id, first_name, last_name, subscribed_to_all) VALUES (%s, %s, %s)'
                    , (update.message.chat.id, update.message.chat.first_name, update.message.chat.last_name, True))
            elif not row[1]:
                curs.execute('UPDATE subscribers SET subscribed_to_all = TRUE WHERE id = %s'
                    , (update.message.chat.id,))
    curs.close()
    conn.close()
    update.message.reply_text('Вы подписались на все.' + str(update.message.chat))

def unsubscribe_from_all(update):
    update.message.reply_text('Вы отменили подписку на все')

updater = Updater(TOKEN)

# add handlers
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(MessageHandler(Filters.text, handler))

updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

updater.bot.setWebhook("https://whatsnew1cbot.herokuapp.com/" + TOKEN)
updater.idle()