import db
import feedparser as fp
import psycopg2
import os
import urllib.parse as urlparse
import telegram
from telegram.ext import Updater

def get_new_feeds(last_guid):
    feed = fp.parse('https://news.webits.1c.ru/news/updates/rss')
    items = feed['items']
    result = []
    for item in items:
        if item.id == last_guid:
            break
        result.append(item)
    return result

def get_feed_struct(feed):
    result = {}
    result['title'] = feed.title
    result['description'] = feed.description
    result['published'] = feed.published
    products = []
    for tag in feed['tags']:
        if tag['term'] and tag['term'].startswith('Продукт='):
            products.append(tag['term'].replace('Продукт=', ''))
    result['products'] = products
    return result

def get_last_guid():
    last_guid = None
    db_conn_params = db.get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT last_guid FROM bot_params LIMIT 1')
            row = curs.fetchone()
            last_guid = row[0]
    curs.close()
    conn.close()
    return last_guid

def update_last_guid(new_guid, last_guid):
    db_conn_params = db.get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('UPDATE bot_params SET last_guid = %s WHERE last_guid = %s'
                , (new_guid, last_guid))
    curs.close()
    conn.close()

def get_receivers():
    subscribers = []
    db_conn_params = db.get_db_conn_params()
    with psycopg2.connect(dbname=db_conn_params['dbname'], user=db_conn_params['user'], host=db_conn_params['host'], password=db_conn_params['password']) as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT id, subscribed_to_all FROM subscribers')
            rows = curs.fetchall()
            for row in rows:
                subscribers.append({'id': row[0], 'subscribed_to_all': row[1]})
    curs.close()
    conn.close()
    return subscribers

def send_feed(updater, feed, receivers):
    message_text = feed['title'] + '<br>' + feed['description'] + '<br>' + feed['published']
    for receiver in receivers:
        if receiver['subscribed_to_all']:
            updater.bot.send_message(receiver['id'], text=message_text, parse_mode=telegram.ParseMode.HTML)

if __name__ == '__main__':

    TOKEN = os.environ['BOT_TOKEN']
    updater = Updater(TOKEN)
    receivers = get_receivers()
    last_guid = get_last_guid()
    new_feeds = get_new_feeds(last_guid)
    for item in map(get_feed_struct, new_feeds):
        send_feed(updater, item, receivers)
    if len(new_feeds) > 0:
        update_last_guid(new_feeds[0].id, last_guid)