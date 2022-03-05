from datetime import datetime
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
    def get_name(message, account, error=False):
        if error:
            msg = "Пожалуйста, укажите Ваше имя корректно (имя должно содержать только буквы)"
        else:
            msg = "📨 Представьтесь, пожалуйста, как Вас зовут? 🙂\n(Напишите ответное сообщение) 👇👇👇"
        first_dialog = bot.send_message(message.chat.id, msg)
        bot.register_next_step_handler(first_dialog, create_user)


    def create_user(message, account):
        if message.content_type == 'text':
            name = message.text.strip()
            if helpers.name_is_valid(name):
                account.tm_id = message.from_user.id
                account.user.first_name = message.text.strip()
                account.save()
                bot.send_message(message.chat.id, f"❓ {name}, посещаете ли Вы церковь?",
                                 reply_markup=helpers.render_keyboard(constants.STATUS))
            # users = models.RDB()
            # chat_id = message.chat.id
            # tm_id = message.from_user.id

            # m_id = message.id
            # if helpers.name_is_valid(name):
            #     body = users.init_item(chat_id, tm_id, name, m_id)
            #     users.set_item(chat_id, body)
            #     bot.send_message(message.chat.id, f"❓ {name}, посещаете ли Вы церковь?",
            #                      reply_markup=helpers.render_keyboard(constants.STATUS))
            else:
                get_name(message, account=account, error=True)
        else:
            send_welcome(message)


    def forward_trouble(users, message, action=None, admin=False):
        reserved_contact = users.get_item_value(message.chat.id, "contact")
        if admin:
            chat_id = message.chat.id
            msg = (f'❌ ПОЛЬЗОВАТЕЛЬ НЕ ПОЛУЧИЛ КОНСУЛЬТАЦИЮ!\n'
                   f'Заявка №: {chat_id}_{users.get_item_value(chat_id, "last_message_id")}"\n'
                   f'Пользователь: @{message.chat.username}\n'
                   f'Имя: {users.get_item_value(chat_id, "name")}\n'
                   f'Статус (верующий/неверующий): {constants.STATUS.get(users.get_item_value(chat_id, "status"))}\n'
                   f'Доп. контакт: {reserved_contact}\n'
                   f'Тема: {users.get_item_value(chat_id, "action_type")}\n'
                   f'Дата обращения: {users.get_item_value(chat_id, "last_message_date")}\n'
                   f'Сообщение: {users.get_item_value(chat_id, "last_message")}')
        else:
            msg = (f'Заявка №: "{message.chat.id}_{message.id}"\n '
           f'Пользователь: @{message.from_user.username}\n'
           f'Имя: {users.get_item_value(message.chat.id, "name")}\n'
           f'Статус (верующий/неверующий): {constants.STATUS.get(users.get_item_value(message.chat.id, "status"))}\n'
           f'Доп. контакт: {reserved_contact}\n'
           f'Тема: {settings.ACTIONS[action] if action is not None else ""}\n'
           f'Сообщение: {message.text}')

        if not reserved_contact:
            k_wargs = {"reply_markup": helpers.render_keyboard(
                {f'private_{message.chat.id}': "Спросить контакты (⚠️Нажимать только если аккаунт скрыт пользователем)"}
            )}
        else:
            k_wargs = {}

        return msg, k_wargs


    def get_trouble(message, action):
        users = models.RDB()

        manager_chat = models.get_env_value(action)

        msg, k_wargs = forward_trouble(users, message, action)

        msg_log = msg.replace("\n", " - ")
        logging.warning(f'{datetime.now} - in get_trouble - MANAGER - {manager_chat} DATA - {msg_log}')

        bot.reply_to(message,
                     f'{users.get_item_value(message.chat.id, "name")}, Ваше обращение принято в обработку. '
                     f'Мы с вами свяжемся в ближайшее время! 🕰 Благодарим за обращение! 🌷',
                     reply_markup=helpers.returntomainmenu_keyboard())

        users.change_item(message.chat.id, "request", "1")
        users.change_item(message.chat.id, "last_message_id", f"{message.id}")
        users.change_item(message.chat.id, "last_message", message.text)
        users.change_item(message.chat.id, "last_message_date", f"{datetime.now()}")
        users.change_item(message.chat.id, "action_type", f"{settings.ACTIONS[action]}")
        logging.warning(f'{datetime.now} - USER DATA AFTER GET TROUBLE - {users.get_object(message.chat.id)}')

        try:
            bot.send_message(manager_chat, msg, **k_wargs)
            bot.forward_message(manager_chat, message.chat.id, message_id=message.id)
        except telebot.apihelper.ApiTelegramException:
            msg = '⚠️ ДОСТУП БОТА К МЕНЕДЖЕРУ ОГРАНИЧЕН! СЛЕДУЮЩЕЕ ОБРАЩЕНИЕ НЕ ДОСТАВЛЕНО ⬇️\n\n' + msg
            bot.send_message(models.get_env_value('superadmin'), msg, **k_wargs)
            bot.forward_message(models.get_env_value('superadmin'), message.chat.id, message_id=message.id)
            bot.send_message(models.get_env_value('admin'), msg, **k_wargs)
            bot.forward_message(models.get_env_value('admin'), message.chat.id, message_id=message.id)


    @bot.callback_query_handler(func=lambda call: True)
    def query_handler(call):
        if str(call.message.chat.id).startswith('-'):
            return None
        logging.warning(f'{datetime.now} - in query_handler/ Clicked Button - {call.data}')
        try:
            bot.answer_callback_query(callback_query_id=call.id)
            if call.data == 'contact':
                chat_id = call.message.chat.id
                answer = constants.CONTACTS
                bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                bot.send_message(call.message.chat.id, answer,
                                 reply_markup=helpers.returntomainmenu_keyboard(show_website=True), parse_mode="HTML")
            elif call.data in settings.ACTIONS.keys():
                chat_id = call.message.chat.id
                answer = f'Вы выбрали тему:"{settings.ACTIONS[call.data]}"\n\n📨 Опишите, пожалуйста, свою ситуацию более подробно в ответе ОДНИМ текстовым сообщением 👇👇👇'
                sent = bot.send_message(chat_id, answer)
                bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id,
                                              reply_markup=helpers.returntomainmenu_keyboard())
                bot.clear_step_handler(call.message)
                bot.register_next_step_handler(sent, get_trouble, action=call.data)
            elif call.data == 'menu':
                chat_id = call.message.chat.id
                bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                bot.send_message(chat_id, 'Выберите тему для Вашего обращения',
                                 reply_markup=helpers.render_keyboard(settings.ACTIONS, True))
            elif call.data in constants.STATUS.keys():
                chat_id = call.message.chat.id
                users = models.RDB()
                users.change_item(chat_id, "status", str(call.data))

                bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                bot.send_message(chat_id,
                                 f'Приятно познакомиться, {users.get_item_value(chat_id, "name")}! 😉'
                                 f'Спасибо, что уделили время и представились 🙏\n\n'
                                 f'❓На какую тему Ваш вопрос? 👇\n(Все консультации для Вас бесплатны 🔥)',
                                 reply_markup=helpers.render_keyboard(settings.ACTIONS, True))

            elif call.data == 'ignored':
                message = call.message
                chat_id = message.chat.id

                users = models.RDB()
                users.change_item(chat_id, "request", "3")

                msg, k_wargs = forward_trouble(users, message, admin=True)

                bot.send_message(models.get_env_value('admin'), msg, **k_wargs)
                bot.forward_message(models.get_env_value("admin"), chat_id,
                                    message_id=users.get_item_value(chat_id, "last_message_id"))

                bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                answer = 'Ваше обращение отправлено специалисту повторно. Просим прощения за задержку консультации 😔🌷'
                bot.send_message(chat_id, answer, reply_markup=helpers.returntomainmenu_keyboard(show_website=True))
                logging.warning(f'{datetime.now} - Ignored Button - processed')

            elif call.data == 'answered':
                chat_id = call.message.chat.id
                users = models.RDB()
                users.change_item(chat_id, "request", "2")
                bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                answer = ('Благодарим за доверие к нам в Вашей ситуации! 🙏'
                          'При возникновении вопросов всегда готовы Вам помочь! 💒\n\n'
                          'Пусть Господь благословит Вас!')
                bot.send_message(chat_id, answer, reply_markup=helpers.returntomainmenu_keyboard(show_website=True))
                logging.warning(f'{datetime.now} - Answered Button - processed')
            elif call.data.startswith('private_'):
                btn_id = call.data
                manager_chat = call.message.chat.id
                chat_id = btn_id[btn_id.rfind('_') + 1:]
                get_contact = bot.send_message(
                    chat_id,
                    f'⚠️ Ваш профиль в telegram приватный. \n\nНапишите, пожалуйста, в ответе одним сообщением '
                    f'ваш номер телефона или email для связи. 👇👇👇',
                )
                bot.register_next_step_handler(get_contact, additional_contact, manager_chat=manager_chat)
                bot.edit_message_reply_markup(chat_id=manager_chat, message_id=call.message.id, reply_markup=None)
            else:
                pass
        except Exception as err:
            logging.error(f'{datetime.now()} - {helpers._get_detail_exception_info(err)}')


    def additional_contact(message, manager_chat):
        bot.forward_message(manager_chat, message.chat.id, message_id=message.id)
        contact = message.text
        users = models.RDB()
        users.change_item(message.chat.id, "contact", contact)
        bot.reply_to(message,
                     f'Спасибо, {users.get_item_value(message.chat.id, "name")}! Ваш контакт передан, скоро с Вами свяжутся 📲',
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

        account, created = models.Account.objects.get_or_create(chat_id=message.chat.id)
        if created:
            get_name(message, account=account)
        else:
            bot.send_message(message.chat.id, 'Выберите тему для Вашего обращения',
                             reply_markup=helpers.render_keyboard(settings.ACTIONS, True))

    def feedback_checker():
        sleep_time = 1000
        logging.warning(f'{datetime.now()} - start feedback_checker')
        users = models.RDB()
        while True:
            logging.warning(f'{datetime.now()} - start feedback_checker cycle')
            for chat_id in models.db.scan_iter('user:*'):
                if str(chat_id).startswith('-'):
                    return None
                # obj = users.get_object(chat_id)
                request_status = users.get_item_value(chat_id, 'request')
                last_message_date = users.get_item_value(chat_id, 'last_message_date')
                name = users.get_item_value(chat_id, 'name')

                if request_status == '1' and last_message_date:
                    dt_format = '%Y-%m-%d %H:%M:%S.%f'
                    dt = datetime.strptime(last_message_date, dt_format)
                    if abs(datetime.now() - dt).days >= 1:
                        # if abs(datetime.now() - dt).days < 1:
                        try:
                            bot.send_message(chat_id.decode(), f'Здравствуйте, {name}! '
                                                               f'Недавно Вы оставляли обращение для консультации.\n\n'
                                                               f'С Вами связались по Вашему обращению? (выберите соответствующий вариант ниже 👇)',
                                             reply_markup=helpers.render_keyboard(constants.FEEDBACK))
                        except telebot.apihelper.ApiTelegramException:
                            pass
                        users.change_item(chat_id.decode(), "request", "4")
                        logging.warning(
                            f'{datetime.now()} - asking for feedback - USER_ID {users.get_item_value(chat_id, "tm_id")} - '
                            f'CHAT_ID - {chat_id.decode()}')
            logging.warning(
                f'{datetime.now()} - sleep for {sleep_time} seconds')
            sleep(sleep_time)

    logging.warning(f'{datetime.now()} - starting THREAD')
    Thread(target=feedback_checker).start()
    logging.warning(f'{datetime.now()} - starting BOT')
    bot.polling()
