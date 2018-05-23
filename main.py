import os
import psycopg2
import telebot
import urllib.parse as urlparse
import sys
from telebot import types
from flask import Flask, request
import logging

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
bot = telebot.TeleBot(TOKEN)
print('bot starting')
server = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Hello, ' + message.from_user.first_name)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, message.text)

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    print('webhook!')
    bot.remove_webhook()
    bot.set_webhook(url='https://whatsnew1cbot.herokuapp.com/' + TOKEN)
    return "!", 200

#if __name__ == "__main__":
server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8000)))