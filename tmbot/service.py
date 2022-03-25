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


def validated_bot(bot):
    return isinstance(bot, models.Settings)

def init_bot(bot, city_name):
    logfile = str(settings.BASE_DIR / 'logs' / f'main_{city_name}.log')
    logging.basicConfig(filename=logfile, filemode='a')

    current_bot = models.Settings.objects.filter(bot_token=bot.token).first()

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
            else:
                get_name(message, error=True)
        else:
            send_welcome(message)


    def forward_trouble(account: models.Account, message, action, admin=False):
        chat_id = message.chat.id
        last_message = account.message_set.filter(subcategory=action).last()
        if admin:
            msg = (f'❌ ПОЛЬЗОВАТЕЛЬ НЕ ПОЛУЧИЛ КОНСУЛЬТАЦИЮ!\n'
                   f'Заявка №: {last_message.pk}"\n'
                   f'Пользователь: @{message.chat.username}\n'
                   f'Имя: {account.name}\n'
                   f'Статус (верующий/неверующий): {account.get_faith_status_display()}\n'
                   f'Доп. контакт: {account.contact}\n'
                   f'Тема: {action.interface_name }\n'
                   f'Дата обращения: {last_message.date_create}\n'
                   f'Сообщение: {last_message.last_message}')
        else:
            msg = (f'Заявка №: "{last_message.pk}"\n'
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
        sent = bot.send_message(call.message.chat.id, answer,
                                reply_markup=helpers.returntomainmenu_keyboard(current_bot=current_bot))
        # bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id,
        #                               reply_markup=helpers.returntomainmenu_keyboard())
        # bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        bot.clear_step_handler(call.message)
        bot.register_next_step_handler(sent, get_trouble, action=action)

    def subcategory_proceed(call, data):
        answer = f'Вы выбрали пункт: "{current_bot.subcategories()[data]}"\n\n' \
                 f'📨 Опишите, пожалуйста, свою ситуацию в ответе ОДНИМ текстовым сообщением 👇👇👇'
        action = models.SubCategories.objects.filter(button_name=data, parent_category__city=current_bot).first()
        consult_processing(call, answer, action)



    @bot.callback_query_handler(func=lambda call: True)
    def query_handler(call):
        if str(call.message.chat.id).startswith('-'):
            return None
        logging.warning(f'{datetime.now} - in query_handler/ Clicked Button - {call.data}')
        try:
            chat_id = call.message.chat.id
            bot.answer_callback_query(callback_query_id=call.id)
            if current_bot:
                if call.data == 'contact':
                    # показать контакты
                    answer = current_bot.contacts
                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                    bot.delete_message(chat_id=chat_id, message_id=call.message.id)
                    bot.send_message(call.message.chat.id, answer,
                                         reply_markup=helpers.returntomainmenu_keyboard(
                                             show_website=True, current_bot=current_bot), parse_mode="HTML")
                elif call.data in current_bot.menu_as_dict().keys():
                    # нажали на пункт главного меню
                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                    bot.delete_message(chat_id=chat_id, message_id=call.message.id)
                    subcategories = list(current_bot.mainmenu_set.filter(
                        button_name=call.data).order_by('subcategories__order').values_list(
                        'subcategories__button_name', 'subcategories__interface_name'))
                    if len(subcategories) == 1:
                        # если в пункте главного меню одна подкатегория - сразу выполняем обработку подкатегории
                        subcategory_proceed(call, subcategories[0][0])
                    else:
                        # иначе выводим список подкатегорий
                        subcategories = {button: interface for button, interface in subcategories}
                        subcategories['backtomenu'] = 'Назад'
                        bot.send_message(chat_id, f"Выберите тему:",
                                         reply_markup=helpers.render_keyboard(subcategories))

                elif call.data in current_bot.subcategories(kind='consult').keys():
                    # если нажали на подкатегория меню
                    subcategory_proceed(call, call.data)
                elif call.data in constants.STATUS.keys():
                    # обработка отношения к вере
                    account = models.Account.objects.filter(chat_id=chat_id).first()
                    if not account:
                        return
                    account.faith_status = call.data
                    account.save()

                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                    bot.delete_message(chat_id=chat_id, message_id=call.message.id)
                    bot.send_message(chat_id,
                                     f'Приятно познакомиться, {account.name}! 😉'
                                     f'Спасибо, что уделили время и представились 🙏\n\n'
                                     f'❓На какую тему Ваш вопрос? 👇\n(Все консультации для Вас бесплатны 🔥)',
                                     reply_markup=helpers.render_keyboard(current_bot.menu_as_dict(), True))

                elif call.data.startswith('ignored_'):
                    # если менеджер не связался с пользователем по вопросу (нажимает пользователь)
                    message_pk = helpers.get_id(call.data)

                    message_obj = models.Message.objects.filter(pk=message_pk).first()
                    message_obj.request_status = 4
                    message_obj.save()

                    msg, k_wargs = forward_trouble(message_obj.account, call.message, message_obj.subcategory, admin=True)

                    bot.send_message(models.UppperSettings.objects.filter().first().superadmin.chat_id, msg, **k_wargs)
                    try:
                        bot.send_message(current_bot.pastor.chat_id, msg, **k_wargs)
                        bot.forward_message(current_bot.pastor.chat_id, chat_id,
                                        message_id=message_obj.last_msg_id)
                    except Exception as error:
                        bot.send_message(models.UppperSettings.objects.filter().first().superadmin.chat_id,
                                         f'ошибка отправки сообщения пастору: {error}',
                                         **k_wargs)

                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                    bot.delete_message(chat_id=chat_id, message_id=call.message.id)
                    answer = 'Ваше обращение отправлено специалисту повторно. Просим прощения за задержку консультации 😔🌷'
                    bot.send_message(chat_id, answer, reply_markup=helpers.returntomainmenu_keyboard(show_website=True,
                                                                                                     current_bot=current_bot))
                    logging.warning(f'{datetime.now} - Ignored Button - processed')

                elif call.data.startswith('answered_'):
                    # если менеджер связался с пользователем по вопросу (нажимает пользователь)
                    message_pk = helpers.get_id(call.data)

                    message_obj = models.Message.objects.filter(pk=message_pk).first()
                    message_obj.request_status = 3
                    message_obj.save()

                    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                    bot.delete_message(chat_id=chat_id, message_id=call.message.id)
                    answer = ('Благодарим за доверие к нам в Вашей ситуации! 🙏'
                              'При возникновении вопросов всегда готовы Вам помочь! 💒\n\n'
                              'Пусть Господь благословит Вас!')
                    bot.send_message(chat_id, answer, reply_markup=helpers.returntomainmenu_keyboard(show_website=True,
                                                                                                     current_bot=current_bot))
                    logging.warning(f'{datetime.now} - Answered Button - processed')
                elif call.data.startswith('private_'):
                    # если контакт пользователя приватный и менеджер не может с ним связаться - запрашиваем доп контакт, нажимает менеджер
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
                    # не удаляем предыдущее сообщение, так как оно важно для истории сообщений в чате
                else:
                    # отображаем главное меню или спрашиваем статус веры, если нажата кнопка "главное меню" или пришла необрабатываемая команда
                    bot.clear_step_handler(call.message)
                    account = models.Account.objects.filter(chat_id=chat_id).first()
                    if not account.faith_status:
                        # если по каким-то причинам оборвался процесс знакомства и пользователь переходит к главному меню
                        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                        bot.delete_message(chat_id=chat_id, message_id=call.message.id)
                        bot.send_message(chat_id, f"❓ {account.name}, посещаете ли Вы церковь?",
                                         reply_markup=helpers.render_keyboard(constants.STATUS))
                    else:
                        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id, reply_markup=None)
                        # не удаляем предыдущее сообщение, чтобы у пользователя осталось предыдущее сообщение в истории
                        # (например, если это было обращение и в ответ бот отправил статус заявки, пользователю важно ее видеть)
                        if call.data == 'backtomenu':
                            bot.delete_message(chat_id=chat_id, message_id=call.message.id)
                        menu = current_bot.menu_as_dict()
                        bot.send_message(chat_id, '🔸 ГЛАВНОЕ МЕНЮ 🔸',
                                         reply_markup=helpers.render_keyboard(menu, True))
                    if not account.cities.filter(city=current_bot.city).exists():
                        account.cities.add(current_bot)
            else:
                return
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

        if not validated_bot(current_bot):
            bot.send_message(message.chat.id, f"К сожалению, в данный момент бот не работает.")
            try:
                superadmin = models.UppperSettings.objects.filter().first()
                bot.send_message(superadmin.superadmin.chat_id, f"Не найден бот {current_bot} /start")
            except:
                pass
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
            acc = account.first()
            if not acc.cities.filter(city=current_bot.city).exists():
                acc.cities.add(current_bot)
            if not account.first().faith_status:
                bot.send_message(message.chat.id, f"❓ {acc.name}, посещаете ли Вы церковь?",
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

        while True:
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
                        bot.send_message(chat_id, f'Здравствуйте, {name}! '
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

    # logging.warning(f'{datetime.now()} - starting THREAD')
    # Thread(target=feedback_checker).start()

    while True:
        logging.warning(f'{datetime.now()} - starting BOT')
        try:
            bot.polling(none_stop=True)
        except Exception as err:
            logging.warning(f'{datetime.now()} - {helpers._get_detail_exception_info(err)}')
            sleep(5)

    # bot.polling()
