from django.db import models
from django.contrib.auth.models import User
# from django.contrib.postgres.fields import JSONField

import os
from redis import Redis
from tmbot.constants import REQUEST_STATUS, FAITH_STATUS




# Create your models here.


class UppperSettings(models.Model):
    superadmin = models.ForeignKey('Account', on_delete=models.CASCADE, verbose_name="Суперадмин")


class City(models.Model):
    city = models.CharField(max_length=20, verbose_name="Город")

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"

    def __str__(self):
        return f'{self.city}'


class Settings(models.Model):
    city = models.OneToOneField(City, null=True, on_delete=models.SET_NULL, verbose_name="Город")
    admin = models.ForeignKey('Account', on_delete=models.CASCADE, verbose_name="Администратор", related_name='admin')
    pastor = models.ForeignKey('Account', on_delete=models.CASCADE, verbose_name="Пастор", related_name='pastor')
    bot_token = models.CharField(max_length=255, default=None, null=True, blank=True, verbose_name="bot token")
    contacts = models.TextField(null=True, blank=True, verbose_name="Текст с контактами")
    greeting = models.TextField(null=True, blank=True, verbose_name="Текст приветствия")
    greeting_cover = models.FileField(upload_to='static/', blank=True, default=None, verbose_name="Обложка")

    class Meta:
        verbose_name_plural = "Настройки города"

    def __str__(self):
        return f'{self.city}'


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    tm_id = models.CharField(max_length=20, verbose_name="ID в телеграме")
    chat_id = models.CharField(max_length=20, verbose_name="Chat ID в телеграме")
    username = models.CharField(max_length=50, default="", null=True, blank=True, verbose_name="Username в телеграме")
    faith_status = models.PositiveSmallIntegerField(choices=FAITH_STATUS, default=0,verbose_name='Отношение к вере')
    contact = models.CharField(max_length=200, default="", null=True, blank=True, verbose_name="Дополнительный контакт")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователь"

    def __str__(self):
        return f'{self.user.first_name} - {self.tm_id}'


class MainMenu(models.Model):
    button_name = models.CharField(max_length=20, verbose_name="Ключ (англ)")
    interface_name = models.CharField(max_length=50, verbose_name="Наименование пункта меню (рус)")
    city = models.ForeignKey(City, null=True, on_delete=models.SET_NULL, verbose_name="Город")
    order = models.PositiveSmallIntegerField(verbose_name="порядок отображения в Телеграме", default=10)

    class Meta:
        verbose_name = "Главное меню"
        verbose_name_plural = "Главное меню"

    def actions(self):
        """ forms dict from button_name as key and interface name as value """
        pass

    def __str__(self):
        return f'{self.city} - {self.interface_name}'


class SubCategories(models.Model):
    parent_category = models.ForeignKey(MainMenu, null=True, blank=True, on_delete=models.SET_NULL,
                                        verbose_name="Относится к пункту главного меню")
    button_name = models.CharField(max_length=20, verbose_name="Ключ (англ)")
    interface_name = models.CharField(max_length=50, verbose_name="Наименование пункта меню (рус)")
    order = models.PositiveSmallIntegerField(verbose_name="порядок отображения в Телеграме")
    manager = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL,
                                verbose_name="Менеджер категории")

    class Meta:
        verbose_name = "Подпункт меню"
        verbose_name_plural = "Подпункты меню"
        unique_together = ['order', 'parent_category']

    def __str__(self):
        return f'{self.parent_category.interface_name} - {self.interface_name} - {self.parent_category.city}'


class Message(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="Пользователь")
    category = models.ForeignKey(SubCategories, on_delete=models.DO_NOTHING, )
    last_msg_id = models.CharField(max_length=20, verbose_name="ID последнего сообщения в телеграме")
    last_message = models.CharField(max_length=20, verbose_name="Тело последнего сообщения в телеграме")
    date_create = models.DateTimeField(auto_now=True)
    request_status = models.PositiveSmallIntegerField(verbose_name="Код статуса ответа на обращение", choices=REQUEST_STATUS)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def __str__(self):
        return f'{self.category.parent_category.city} - {self.account.user.first_name} - {self.category.interface_name}'

""""""""""""""""""""""""""""""


def get_env_value(key):
    return os.environ.get(key)


db = Redis.from_url(get_env_value('REDIS'))


def remove_db():
    for key in db.scan_iter('*'):
        db.delete(key)


class RDB():
    def init_item(self, chat_id, tm_id, name, m_id):
        structure = {"tm_id": tm_id,
                     "name": name,
                     "chat_id": chat_id,
                     "last_message_id": m_id,
                     "request": 0,
                     }

        return structure

    def set_item(self, chat_id, body: dict):
        for key, value in body.items():
            db.hset(chat_id, key, value)
        # return db.set(chat_id, body)

    def get_item_value(self, chat_id, key):
        if value := db.hget(chat_id, key):
            return value.decode()
        return None

    def get_object(self, chat_id):
        return db.hgetall(chat_id)

    def change_item(self, chat_id: int, key: str, val: str):
        db.hset(chat_id, key, val)

    def remove_all(self):
        for key in db.scan_iter('*'):
            db.delete(key)
