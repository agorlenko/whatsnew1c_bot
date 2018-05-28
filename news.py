import os
from telegram.ext import Updater

TOKEN = os.environ['BOT_TOKEN']

updater = Updater(TOKEN)

updater.bot.send_message(chat_id=410816255, text='Привет!')
