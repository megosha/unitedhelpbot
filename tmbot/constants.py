STATUS = {"1": 'Хожу в церковь Благословение',
          "2": 'Хожу в другую церковь',
          "3": 'Не хожу в церковь, в Бога верю',
          "4": 'Не верю в Бога',
          "5": 'Нет моего варианта'
          }  # 0, 'Неизвестно'

FAITH_STATUS = ((0, 'Неизвестно'),
                (1, 'Хожу в церковь Благословение'),
          (2, 'Хожу в другую церковь'),
          (3, 'Не хожу в церковь, в Бога верю'),
          (4, 'Не верю в Бога'),
          (5, 'Нет моего варианта')
                )


REQUEST_STATUS = ((0, 'Нет активных обращений'),  # конечный статус
            (1, 'Обращение создано'),
           (2, 'Обращение передано'),
           (3, 'Обращение отвечено (вопрос решён)'),  # конечный статус
           (4, 'Обращение не отвечено (вопрос не решён)'),
           (5, 'Не получен ответ о завершении вопроса'),  # конечный статус

           )

ACTION_TYPE = (('consult', 'Ручная'), ('automatic', 'Автоматическая'))
""" 
    Ручная - универсальная обработка обращений (консультации), 
    автоматическая - оригинальный код обработки действия
"""


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

