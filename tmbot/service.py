from datetime import datetime, timedelta
import logging
# from pathlib import Path
from threading import Thread

import telebot
from django.conf import settings

from tmbot import models
from tmbot import constants
from tmbot import helpers

from time import sleep


BASE_DIR = settings.BASE_DIR
logfile = str(BASE_DIR / 'logs' / 'main.log')
logging.basicConfig(filename=logfile, filemode='a')


def init_bot(bot):
    current_bot = models.Settings.objects.filter(bot_token=bot.token).first()
    #todo validate current bot instance and existance else send message that bot works incorrect
    def get_name(message, error=False):
        if error:
            msg = "Пожалуйста, укажите Ваше имя корректно (имя должно содержать только буквы)"
        else:
            msg = "📨 Представьтесь, пожалуйста, как Вас зовут? 🙂\n(Напишите ответное сообщение) 👇👇👇"
        first_dialog = bot.send_message(message.chat.id, msg)
        bot.register_next_step_handler(first_dialog, create_user)


    def create_user(message):
        if message.content_type == 'text':
            name = message.text.strip()
            if helpers.name_is_valid(name):
                account = models.Account.objects.create(name=name, tm_id=message.from_user.id, chat_id=message.chat.id)
                if message.from_user.username:
                    account.username = message.from_user.username
                    account.save()
                bot.send_message(message.chat.id, f"❓ {name}, посещаете ли Вы церковь?",
                                 reply_markup=helpers.render_keyboard(constants.STATUS))
                #TODO в меню проверять, есть ли статус, запрашивать перед обработкой
                #TODO удалять предыдущие сообщения
            else:
                get_name(message, error=True)
        else:
            send_welcome(message)


    def forward_trouble(account: models.Account, message, action, admin=False):
        chat_id = message.chat.id
        last_message = account.message_set.filter(subcategory=action).last()
        if admin:
            msg = (f'❌ ПОЛЬЗОВАТЕЛЬ НЕ ПОЛУЧИЛ КОНСУЛЬТАЦИЮ!\n'
                   f'Заявка №: {chat_id}_{last_message.last_message_id}"\n'
                   f'Пользователь: @{message.chat.username}\n'
                   f'Имя: {account.name}\n'
                   f'Статус (верующий/неверующий): {account.get_faith_status_display()}\n'
                   f'Доп. контакт: {account.contact}\n'
                   f'Тема: {action.interface_name }\n'
                   f'Дата обращения: {last_message.date_create}\n'
                   f'Сообщение: {last_message.last_message}')
        else:
            msg = (f'Заявка №: "{chat_id}_{last_message.last_msg_id}"\n'
           f'Пользователь: @{message.chat.username}\n'
           f'Имя: {account.name}\n'
           f'Статус (верующий/неверующий): {account.get_faith_status_display()}\n'
           f'Доп. контакт: {account.contact}\n'
           f'Тема: {action.interface_name }\n'
           f'Сообщение: {last_message.last_message}')

        if not account.contact:
            k_wargs = {"reply_markup": helpers.render_keyboard(
                {f'private_{chat_id}': "Спросить контакты (⚠️Нажимать только если аккаунт скрыт пользователем)"}
            )}
        else:
            k_wargs = {}

        return msg, k_wargs


    def get_trouble(message, action):
        chat_id = message.chat.id
        account = models.Account.objects.filter(chat_id=chat_id).first()
        manager_chat = action.manager
        params = {'account':account,
                  "last_msg_id":message.id,
                  "last_message":message.text,
                  "request_status":1,
                  'subcategory':action}
        last_message = models.Message.objects.create(**params)

        msg, k_wargs = forward_trouble(account, message, action)

        msg_log = msg.replace("\n", " - ")
        logging.warning(f'{datetime.now} - in get_trouble - MANAGER - {manager_chat} DATA - {msg_log}')

        bot.reply_to(message,
                     f'{account.name}, Ваше обращение принято в обработку. '
                     f'Мы с вами свяжемся в ближайшее время! 🕰 Благодарим за обращение! 🌷',
                     reply_markup=helpers.returntomainmenu_keyboard())


        last_message.request_status = 2
        last_message.save()
        logging.warning(f'{datetime.now} - USER DATA AFTER GET TROUBLE - {account.chat_id}')

        try:
            bot.send_message(manager_chat.tm_id, msg, **k_wargs)
            bot.forward_message(manager_chat.tm_id, chat_id, message_id=message.id)
        except telebot.apihelper.ApiTelegramException:
            msg = '⚠️ ДОСТУП БОТА К МЕНЕДЖЕРУ ОГРАНИЧЕН! СЛЕДУЮЩЕЕ ОБРАЩЕНИЕ НЕ ДОСТАВЛЕНО ⬇️\n\n' + msg
            superadmin = models.UppperSettings.objects.filter().first()
            bot.send_message(superadmin.superadmin.tm_id, msg, **k_wargs)
            bot.forward_message(superadmin.superadmin.tm_id, chat_id, message_id=message.id)
            bot.send_message(current_bot.pastor.tm_id, msg, **k_wargs)
            bot.forward_message(current_bot.pastor.tm_id, chat_id, message_id=message.id)

    def consult_processing(call, answer, action):
        sent = bot.send_message(call.message.chat.id, answer)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id,
                                      reply_markup=helpers.returntomainmenu_keyboard())
        bot.clear_step_handler(call.message)
        bot.register_next_step_handler(sent, get_trouble, action=action)

    def subcategory_proceed(call, data):
        answer = f'Вы выбрали пункт: "{current_bot.subcategories()[data]}"\n\n' \
                 f'📨 Опишите, пожалуйста, свою ситуацию в ответе ОДНИМ текстовым сообщением 👇👇👇'
        action = models.SubCategories.objects.filter(button_name=data).first()
        consult_processing(call, answer, action)


    @bot.callback_query_handler(func=lambda call: True)
    def query_handler(call):
        if str(call.message.chat.id).startswith('-'):
            return None
        logging.warning(f'{datetime.now} - in query_handler/ Clicked Button - {call.data}')
        try:
            chat_id = call.message.chat.id
            bot.answer_callback_query(callback_query_id=call.id)
            if call.data == 'contact':
                if current_bot:
                    answer = current_bot.contacts
                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                    bot.send_message(call.message.chat.id, answer,
                                     reply_markup=helpers.returntomainmenu_keyboard(
                                         show_website=True, current_bot=current_bot), parse_mode="HTML")
                #todo else return menu

            elif call.data in current_bot.menu_as_dict().keys():
                # bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                subcategories = list(current_bot.mainmenu_set.filter(button_name=call.data).values_list(
                    'subcategories__button_name', 'subcategories__interface_name'))
                if len(subcategories) == 1:
                    subcategory_proceed(call, subcategories[0][0])
                else:
                    subcategories = {button: interface for button, interface in subcategories}
                    bot.send_message(chat_id, f"qwe",
                                     reply_markup=helpers.render_keyboard(subcategories))

            elif call.data in current_bot.subcategories(kind='consult').keys():
                subcategory_proceed(call, call.data)
            # elif call.data == 'menu':
            #     account = models.Account.objects.filter(chat_id=chat_id).first()
            #     if not account.faith_status:
            #         bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
            #         bot.send_message(chat_id, f"❓ {account.name}, посещаете ли Вы церковь?",
            #                          reply_markup=helpers.render_keyboard(constants.STATUS))
            #     else:
            #         bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
            #         menu = current_bot.menu_as_dict()
            #         bot.send_message(chat_id, 'Выберите тему для Вашего обращения',
            #                          reply_markup=helpers.render_keyboard(menu, True))
            elif call.data in constants.STATUS.keys():
                account = models.Account.objects.filter(chat_id=chat_id).first()
                if not account:
                    return
                account.faith_status = call.data
                account.save()

                bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                bot.send_message(chat_id,
                                 f'Приятно познакомиться, {account.name}! 😉'
                                 f'Спасибо, что уделили время и представились 🙏\n\n'
                                 f'❓На какую тему Ваш вопрос? 👇\n(Все консультации для Вас бесплатны 🔥)',
                                 reply_markup=helpers.render_keyboard(settings.ACTIONS, True))

            elif call.data.startswith('ignored_'):
                message_pk = helpers.get_id(call.data)

                message_obj = models.Message.objects.filter(pk=message_pk).first()
                message_obj.request_status = 4
                message_obj.save()

                msg, k_wargs = forward_trouble(message_obj.account, call.message, message_obj.subcategory, admin=True)

                bot.send_message(models.UppperSettings.objects.filter().first().chat_id, msg, **k_wargs)
                bot.send_message(current_bot.pastor.chat_id, msg, **k_wargs)
                bot.forward_message(current_bot.pastor.chat_id, chat_id,
                                    message_id=message_obj.last_msg_id)

                bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                answer = 'Ваше обращение отправлено специалисту повторно. Просим прощения за задержку консультации 😔🌷'
                bot.send_message(chat_id, answer, reply_markup=helpers.returntomainmenu_keyboard(show_website=True,
                                                                                                 current_bot=current_bot))
                logging.warning(f'{datetime.now} - Ignored Button - processed')

            elif call.data.startswith('answered_'):
                message_pk = helpers.get_id(call.data)

                message_obj = models.Message.objects.filter(pk=message_pk).first()
                message_obj.request_status = 3
                message_obj.save()

                bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                answer = ('Благодарим за доверие к нам в Вашей ситуации! 🙏'
                          'При возникновении вопросов всегда готовы Вам помочь! 💒\n\n'
                          'Пусть Господь благословит Вас!')
                bot.send_message(chat_id, answer, reply_markup=helpers.returntomainmenu_keyboard(show_website=True,
                                                                                                 current_bot=current_bot))
                logging.warning(f'{datetime.now} - Answered Button - processed')
            elif call.data.startswith('private_'):
                btn_id = call.data
                manager_chat = call.message.chat.id
                chat_id = helpers.get_id(btn_id)
                get_contact = bot.send_message(
                    chat_id,
                    f'⚠️ Ваш профиль в telegram приватный. \n\nНапишите, пожалуйста, в ответе одним сообщением '
                    f'ваш номер телефона или email для связи. 👇👇👇',
                )
                bot.register_next_step_handler(get_contact, additional_contact, manager_chat=manager_chat)
                bot.edit_message_reply_markup(chat_id=manager_chat, message_id=call.message.id, reply_markup=None)
            else:
                account = models.Account.objects.filter(chat_id=chat_id).first()
                if not account.faith_status:
                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                    bot.send_message(chat_id, f"❓ {account.name}, посещаете ли Вы церковь?",
                                     reply_markup=helpers.render_keyboard(constants.STATUS))
                else:
                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                    menu = current_bot.menu_as_dict()
                    bot.send_message(chat_id, 'Выберите тему для Вашего обращения',
                                     reply_markup=helpers.render_keyboard(menu, True))
        except Exception as err:
            logging.error(f'{datetime.now()} - {helpers._get_detail_exception_info(err)}')


    def additional_contact(message, manager_chat):
        bot.forward_message(manager_chat, message.chat.id, message_id=message.id)
        contact = message.text

        models.Account.objects.filter(chat_id=message.chat.id).update(contact=contact)

        bot.reply_to(message,
                     f'Ваш контакт передан, скоро с Вами свяжутся 📲',
                     reply_markup=helpers.returntomainmenu_keyboard())


    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        if str(message.chat.id).startswith('-'):
            return None
        logging.warning(f'{datetime.now} - clicked start Button')

        if message.from_user.is_bot:
            return

        local_bot = models.Settings.objects.filter(bot_token=bot.token).first()
        if not local_bot:
            return

        bot.reply_to(message, local_bot.greeting)
        if local_bot.greeting_cover:
            img = open(f'{local_bot.greeting_cover.path}', 'rb')
            bot.send_photo(message.chat.id, img)

        account = models.Account.objects.filter(chat_id=message.chat.id)
        if not account.exists():
            get_name(message)
        else:
            if not account.first().faith_status:
                bot.send_message(message.chat.id, f"❓ {account.first().name}, посещаете ли Вы церковь?",
                                 reply_markup=helpers.render_keyboard(constants.STATUS))
            else:
                menu = current_bot.menu_as_dict()
                bot.send_message(message.chat.id, 'Выберите тему для Вашего обращения',
                             reply_markup=helpers.render_keyboard(menu, True))

    def feedback_checker():
        sleep_time = 1000
        logging.warning(f'{datetime.now()} - start feedback_checker')


        params = {'subcategory__parent_category__city__city':current_bot.city,
                  'date_create__lte':datetime.now()-timedelta(days=1),
                  'request_status':2,
                  }
        messages = models.Message.objects.filter(**params)

        while True:
            logging.warning(f'{datetime.now()} - start feedback_checker cycle')

            for message in messages:
                chat_id = message.account.chat_id
                name = message.account.name
                subcategory_title = message.subcategory.interface_name

                expect_answer = models.Message.objects.filter(account=message.account, request_status=5).exists()
                if not expect_answer:
                    FEEDBACK = {f"answered_{message.pk}": "✅  Да, со мной связались",
                                f"ignored_{message.pk}": "❌  Нет, я не получил ответа"
                                }
                    try:
                        bot.send_message(chat_id, f'Здравствуйте, {name}! '
                                                  f'Недавно Вы обратились по теме «{subcategory_title}».\n\n'
                                                  f'С Вами связались по Вашему обращению? (выберите соответствующий вариант ниже 👇)',
                                         reply_markup=helpers.render_keyboard(FEEDBACK))
                    except telebot.apihelper.ApiTelegramException:
                        pass

                    message.request_status = 5
                    message.save()
                    logging.warning(
                        f'{datetime.now()} - asking for feedback - USER_ID {message.account.tm_id} - '
                        f'CHAT_ID - {chat_id}')
            logging.warning(
                f'{datetime.now()} - sleep for {sleep_time} seconds')
            sleep(sleep_time)

    logging.warning(f'{datetime.now()} - starting THREAD')
    Thread(target=feedback_checker).start()
    logging.warning(f'{datetime.now()} - starting BOT')
    bot.polling()
