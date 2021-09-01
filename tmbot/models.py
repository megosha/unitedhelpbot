from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField

import os
from redis import Redis


# from helpers import get_env_value


# Create your models here.


class City(models.Model):
    city = models.CharField(max_length=20, verbose_name="Город")

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"


class Setting(models.Model):
    city = models.ForeignKey(City, null=True, on_delete=models.SET_NULL, verbose_name="Город")
    bot_token = models.CharField(max_length=100, default=None, null=True, blank=True, verbose_name="bot token")
    contacts = models.TextField(null=True, blank=True, verbose_name="Текст с контактами")
    greeting = models.TextField(null=True, blank=True, verbose_name="Текст приветствия")

    class Meta:
        verbose_name = "Настройки"


class MainMenu(models.Model):
    button_name = models.CharField(max_length=20, verbose_name="Ключ (англ)")
    interface_name = models.CharField(max_length=30, verbose_name="Наименование пункта меню (рус)")
    city = models.ForeignKey(City, null=True, on_delete=models.SET_NULL, verbose_name="Город")
    order = models.PositiveSmallIntegerField(verbose_name="порядок отображения в Телеграме", unique=True)

    class Meta:
        verbose_name = "Главное меню"
        verbose_name_plural = "Главные меню"

    def actions(self):
        """ forms dict from button_name as key and interface)name as value """
        ...


class FaithStatus(models.Model):
    code = models.PositiveSmallIntegerField(verbose_name="Код статуса", unique=True)
    description = models.CharField(max_length=50, verbose_name="Описание статуса (Отображается в телеграме)")

    class Meta:
        verbose_name = "Позиция в вере"
        verbose_name_plural = "Позиция в вере"


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    tm_id = models.CharField(max_length=20, verbose_name="ID в телеграме")
    chat_id = models.CharField(max_length=20, verbose_name="Chat ID в телеграме")
    username = models.CharField(max_length=50, default=None, null=True, blank=True, verbose_name="Username в телеграме")
    faith_status = models.ForeignKey(FaithStatus, default=None, null=True, blank=True, on_delete=models.DO_NOTHING,
                                     verbose_name='Позиция в вере')
    contact = models.CharField(max_length=200, default=None, null=True, blank=True, verbose_name="Дополнительный контакт")


class RequestStatus(models.Model):
    code = models.PositiveSmallIntegerField(verbose_name="Код статуса ответа на обращение", unique=True)
    description = models.CharField(max_length=50, verbose_name="Описание статуса")


# class Message(models.Model):
#     account = models.ForeignKey()
#     category = models.ForeignKey()
#     last_msg_id =
#     last_message =
#     date_create =
#     request_status =


class SubCategories(models.Model):
    parent_category = models.ForeignKey(MainMenu, default=None, null=True, blank=True, on_delete=models.SET_NULL,
                                        verbose_name="Относится к пункту главного меню")
    button_name = models.CharField(max_length=20, verbose_name="Ключ (англ)")
    interface_name = models.CharField(max_length=30, verbose_name="Наименование пункта меню (рус)")
    order = models.PositiveSmallIntegerField(verbose_name="порядок отображения в Телеграме")
    manager = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL,
                                verbose_name="Менеджер категории")

    class Meta:
        verbose_name = "Главное меню"
        verbose_name_plural = "Главные меню"
        unique_together = ['order', 'parent_category']


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

    def get_item_value(self, chat_id: int, key):
        if db.hget(chat_id, key):
            return db.hget(chat_id, key).decode()
        return None

    def get_object(self, chat_id):
        return db.hgetall(chat_id)

    def change_item(self, chat_id: int, key: str, val: str):
        db.hset(chat_id, key, val)

    def remove_all(self):
        for key in db.scan_iter('*'):
            db.delete(key)
