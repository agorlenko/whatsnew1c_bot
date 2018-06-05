import db
import json
import os
import psycopg2
import urllib.parse as urlparse
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters

TOKEN = os.environ['BOT_TOKEN']
PORT = int(os.environ.get('PORT', '5000'))

keyboard = [['Подписаться на все', 'Отменить подписку'], ['Подписаться на продукт', 'Мои подписки']]    
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
    elif update.message.text == 'Подписаться на продукт':
        update.message.reply_text('Введите наименование продукта')
    elif update.message.text == 'Мои подписки':
        product_list(update)
    else:
        find_product(update)

def callback_handler(bot, update):
    query = update.callback_query
    if not query:
        return
    handler_params = json.loads(query.data)
    chat_id = query.from_user.id
    if handler_params['operation'] == 'subscribe':
        result = subscribe_to_product(chat_id, handler_params['product_id'])
        if result == 0:
            updater.bot.send_message(chat_id, text='Вы успешно подписались на продукт')
        elif result == 2:
            updater.bot.send_message(chat_id, text='Вы уже подписаны на продукт')
        else:
            updater.bot.send_message(chat_id, text='Не удалось подписаться на продукт')
    elif handler_params['operation'] == 'unsubscribe':
        result = unsubscribe_from_product(chat_id, handler_params['product_id'])
        if result == 0:
            updater.bot.send_message(chat_id, text='Подписка отменена')
        else:
            updater.bot.send_message(chat_id, text='Не удалось отменить подписку')

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

def subscribe_to_product(chat_id, product_id):
    db_conn_params = db.get_db_conn_params()
    result = None
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT id, product_id FROM subscriptions_to_products WHERE id = %s and product_id = %s', (chat_id, product_id))
            row = curs.fetchone()
            if not row:
                curs.execute('INSERT INTO subscriptions_to_products (id, product_id) VALUES (%s, %s)', (chat_id, product_id))
            else:
                result = 2
    curs.close()
    conn.close()
    if not result:
        result = 0
    return result

def unsubscribe_from_all(update):
    db_conn_params = db.get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('DELETE FROM subscribers WHERE id = %s', (update.message.chat.id,))
    curs.close()
    conn.close()
    update.message.reply_text('Подписка на все новости отменена')

def unsubscribe_from_product(chat_id, product_id):
    db_conn_params = db.get_db_conn_params()
    result = None
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('DELETE FROM subscriptions_to_products WHERE id = %s and product_id = %s', (chat_id, product_id))
    curs.close()
    conn.close()
    result = 0
    return result

def find_product(update):
    product_rows = []
    db_conn_params = db.get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT id, name FROM products WHERE name ~* %s', (update.message.text,))
            product_rows = curs.fetchall()
    curs.close()
    conn.close()

    if not product_rows:
        update.message.reply_text('Ничего не нашел')
    elif len(product_rows) > 15:
        update.message.reply_text('Слишком много результатов. Попробуйте уточнить условия поиска.')
    else:
        for row in product_rows:
            keyboard = [[InlineKeyboardButton("Подписаться", callback_data=json.dumps({'operation': 'subscribe', 'product_id': row[0]})),
                InlineKeyboardButton("Отписаться", callback_data=json.dumps({'operation': 'unsubscribe', 'product_id': row[0]}))]]
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

def product_list(update):
    db_conn_params = db.get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT id, subscribed_to_all FROM subscribers WHERE id = %s', (update.message.chat.id,))
            row = curs.fetchone()
            if row and row[1]:
                update.message.reply_text('Вы подписаны на все новости')
            else:
                sql = """
                    SELECT
                        SP.product_id AS product_id,
                        P.name AS product_name
                    FROM subscriptions_to_products AS SP
                        INNER JOIN products AS P
                        ON SP.id = %s SP.product_id = P.id """
                curs.execute(sql, (update.message.chat.id,))
                rows = curs.fetchall()
                for row in rows:
                    keyboard = [[InlineKeyboardButton("Отписаться", callback_data=json.dumps({'operation': 'unsubscribe', 'product_id': row[0]}))]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    update.message.reply_text(row[1], reply_markup=reply_markup)
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
