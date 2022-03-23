import logging
from asyncio import sleep
from datetime import datetime, timedelta

import telebot

from django.core.management.base import BaseCommand

from tmbot import service, models, helpers
from django.conf import settings


class Command(BaseCommand):

    def handle(self, *args, **options):
        logfile = str(settings.BASE_DIR / 'logs' / f'checker.log')
        logging.basicConfig(filename=logfile, filemode='a')

        sleep_time = 1000
        logging.warning(f'{datetime.now()} - start feedback_checker')

        bots = models.Settings.objects.all()
        inited_bots = []
        for bot_obj in bots:
            inited_bots.append(telebot.TeleBot(bot_obj.bot_token))

        while True:
            for index, current_bot in enumerate(bots):
                params = {'subcategory__parent_category__city__city': current_bot.city,
                      'date_create__lte': datetime.now() - timedelta(days=1),
                      'request_status': 2,
                      }

                messages = models.Message.objects.filter(**params)
                logging.warning(f'{datetime.now()} - start feedback_checker cycle - found {messages.count()} messages')

                for message in messages:
                    chat_id = message.account.chat_id
                    name = message.account.name
                    subcategory_title = message.subcategory.interface_name

                    expect_answer = models.Message.objects.filter(subcategory__parent_category__city__city=current_bot.city,
                                                                  account=message.account, request_status=5).exists()
                    if not expect_answer:
                        FEEDBACK = {f"answered_{message.pk}": "✅  Да, со мной связались",
                                    f"ignored_{message.pk}": "❌  Нет, я не получил ответа"
                                    }
                        try:
                            inited_bots[index].send_message(chat_id, f'Здравствуйте, {name}! '
                                                      f'Недавно Вы обратились по теме «{subcategory_title}».\n\n'
                                                      f'С Вами связались по Вашему обращению? (выберите соответствующий вариант ниже 👇)',
                                             reply_markup=helpers.render_keyboard(FEEDBACK))
                        except telebot.apihelper.ApiTelegramException:
                            logging.warning(f'{datetime.now()} - message sending error - {message.pk} pk')

                        message.request_status = 5
                        message.save()
                        logging.warning(
                            f'{datetime.now()} - asking for feedback - USER_ID {message.account.tm_id} - '
                            f'CHAT_ID - {chat_id}')
                logging.warning(
                f'{datetime.now()} - sleep for {sleep_time} seconds')
            sleep(sleep_time)













