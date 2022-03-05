import os
import sys

import telebot
from tmbot.models import get_env_value




def greeting_message():
    return (f'Здравствуйте! Я помощник церкви «Благословение» г. Барнаул ⛪\n\n'
            f'Наша церковь образована в 2009 году.'
            f'\nМиссионеры Артём и Анастасия Торопчины, приехав в Барнаул, стали служить людям Евангелием и добрыми делами ♥️\n\n'
            f'‼️ Мы помогаем решить проблемы:\n'
            f'1) финансовые \n'
            f'2) социальные \n'
            f'3) семейные \n'
            f'4) душевные \n'
            f'5) духовные \nНа сегодняшний день, уже более 1000 человек получили нашу помощь 🤝🙌\n\n'
            f'Помощь мы оказываем БЕСПЛАТНО 🙏\n\n'
            f'📝 Я могу принять Ваше обращение для консультации и с Вами свяжется компетентный служитель церкви 🙋‍♀️'
            )


def name_is_valid(name: str):
    return name.replace('-', '').isalpha() and len(name) <= 100


def render_keyboard(params: dict, standart=False):
    kboard = telebot.types.InlineKeyboardMarkup(row_width=6)
    for k, v in params.items():
        kboard.add(telebot.types.InlineKeyboardButton(text=v, callback_data=k))
    if standart:
        kboard.add(telebot.types.InlineKeyboardButton(text='Показать контакты', callback_data='contact'))
    return kboard


def returntomainmenu_keyboard(show_website=False):
    kboard = telebot.types.InlineKeyboardMarkup()
    if show_website:
        kboard.add(telebot.types.InlineKeyboardButton(text='Перейти на сайт', url=get_env_value("website")))
    kboard.add(telebot.types.InlineKeyboardButton(text='Показать другие функции', callback_data='menu'))
    return kboard


def _get_detail_exception_info(exception_object: Exception):
    """
    Returns the short occurred exception description.
    :param exception_object:
    :return:
    """
    type, value, traceback = sys.exc_info()
    if traceback:
        # import traceback as tb
        # tb.print_tb(traceback, file=sys.stdout)

        return '{message} ({code} in {file}: {line})'.format(
            message=str(exception_object),
            code=exception_object.__class__.__name__,
            file=os.path.split(sys.exc_info()[2].tb_frame.f_code.co_filename)[1],
            line=sys.exc_info()[2].tb_lineno,
        )
    else:
        return f'{str(exception_object)} ({exception_object.__class__.__name__})'