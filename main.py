import db
import os
import psycopg2
import urllib.parse as urlparse
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters

TOKEN = os.environ['BOT_TOKEN']
PORT = int(os.environ.get('PORT', '5000'))

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
    elif update.message.text == 'Подписаться':
        update.message.reply_text('Я обычный')
    else:
        find_product(update)

def callback_handler(update, context):
    updater.bot.send_message(410816255, text='Я колбэк ')
    query = update.callback_query
    updater.bot.send_message(410816255, text='Я колбэк ' + str(query))
    #update.message.reply_text(query.data)

def subscribe_to_all(update):
    db_conn_params = db.get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT id, subscribed_to_all FROM subscribers WHERE id = %s', (update.message.chat.id,))
            row = curs.fetchone()
            if not row:
                curs.execute('INSERT INTO subscribers (id, first_name, last_name, subscribed_to_all) VALUES (%s, %s, %s, %s)'
                    , (update.message.chat.id, update.message.chat.first_name, update.message.chat.last_name, True))
            elif not row[1]:
                curs.execute('UPDATE subscribers SET subscribed_to_all = TRUE WHERE id = %s'
                    , (update.message.chat.id,))
    curs.close()
    conn.close()
    update.message.reply_text('Вы успешно подписались на все новости')

def unsubscribe_from_all(update):
    db_conn_params = db.get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('DELETE FROM subscribers WHERE id = %s', (update.message.chat.id,))
    curs.close()
    conn.close()
    update.message.reply_text('Подписка на все новости отменена')

def find_product(update):
    update.message.reply_text('Ищу продукты...')
    product_rows = []
    db_conn_params = db.get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute("SELECT id, name FROM products WHERE name ~* '.*" + update.message.text + ".*'")
            product_rows = curs.fetchall()
    curs.close()
    conn.close()

    for row in product_rows:
        update.message.reply_text('Что-то нашел...')
        keyboard = [[InlineKeyboardButton("Подписаться", callback_data=row[0]), InlineKeyboardButton("Отписаться", callback_data=row[0])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(row[1], reply_markup=reply_markup)

def add_product(name):
    db_conn_params = db.get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute("SELECT * FROM products WHERE name ~* '.*%s.*'", (name,))
            row = curs.fetchone()
            if not row:
                curs.execute('INSERT INTO products (name) VALUES (%s)'
                    , (name))
    curs.close()
    conn.close()

if __name__ == '__main__':

    updater = Updater(TOKEN)

    # add handlers
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handler))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback_handler))

    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

    updater.bot.setWebhook("https://whatsnew1cbot.herokuapp.com/" + TOKEN)
    updater.idle()
