from tmbot import models


STATUS = {"1": 'Хожу в вашу церковь',
          "2": 'Хожу в другую церковь',
          "3": 'Не хожу в церковь, в Бога верю',
          "4": 'Не верю в Бога',
          "5": 'Нет моего варианта'
          }  # 0, 'Неизвестно'


FEEDBACK = {"answered": "✅  Да, со мной связались",
            "ignored":"❌  Нет, я не получил ответа"
            }


request = ((0, 'Нет активных обращений'),  # конечный статус
           (1, 'Обращение передано'),
           (2, 'Обращение отвечено (вопрос решён)'),  # конечный статус
           (3, 'Обращение не отвечено (вопрос не решён)'),
           (4, 'Не получен ответ о завершении вопроса'),  # конечный статус
           )

CONTACTS = (f'<u><b>НАШИ КОНТАКТЫ</b></u> 👇\n\n'
           f'Сайт: {models.get_env_value("website")}\nАдрес: {models.get_env_value("address")}\n\n'
           f'<b>Подпишись на наши группы!</b> 😉 \n\n'
           f'YouTube: {models.get_env_value("yt")} \n'
           f'ВКонтакте: {models.get_env_value("vk")} \n'
           f'Instagram: {models.get_env_value("ig")} \n'
           f'Одноклассники: {models.get_env_value("ok")} \n'
           f'Telegram: {models.get_env_value("tg")} \n'
           f'Tik Tok: {models.get_env_value("tt")} \n'
           f'Facebook: {models.get_env_value("fb")} \n'
            )

'''
structure = {"987654":
                 {"tm_id": 123456,
                  "username": "uname",  # optional
                  "name": "Ivan",
                  "status": 1,
                  "contact": "891231231223",  # optional
                  "chat_id": 987654,
                  "last_message_id": 48,  # optional
                  "last_message":"123", # optional
                  "last_message_date":datetime,
                  "action_type":action),        # ACTIONS['action'] #optional
                  "request": 0},  # optional
             }
             '''

