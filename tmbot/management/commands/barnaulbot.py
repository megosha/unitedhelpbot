import telebot

from django.core.management.base import BaseCommand

from tmbot import service, models


class Command(BaseCommand):

    def handle(self, *args, **options):
        city = options['city']
        city_settings = models.Settings.objects.filter(city__city=city).first()
        if not city_settings:
            print(f'City {city} not found, available: {list(models.Settings.objects.values_list("city__city", flat=True))}')
            return
        bot = telebot.TeleBot(city_settings.bot_token)
        service.init_bot(bot, city)

    def add_arguments(self, parser):
        parser.add_argument('city', type=str, nargs='?', default='Барнаул')
