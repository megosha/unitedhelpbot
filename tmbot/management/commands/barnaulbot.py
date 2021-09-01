from datetime import datetime
import logging

import telebot

from threading import Thread

from django.conf import settings
from django.core.management.base import BaseCommand

from tmbot import service

logfile = str(settings.BASE_DIR / 'logs' / 'main.log')
logging.basicConfig(filename=logfile, filemode='a')

# bot = telebot.TeleBot(settings.BOT_TOKEN)
bot = service.bot


class Command(BaseCommand):

    def handle(self, *args, **options):
        logging.warning(f'{datetime.now()} - starting THREAD')
        Thread(target=service.feedback_checker).start()
        logging.warning(f'{datetime.now()} - starting BOT')
        # bot.polling(none_stop=True)
        bot.polling()