from django.contrib import admin
from tmbot import models

from django.contrib.auth.models import User


# Register your models here.

@admin.register(models.UppperSettings)
class UppperSettingsAdmin(admin.ModelAdmin):
    list_display = ['superadmin']


@admin.register(models.City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['city']

@admin.register(models.Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['city', 'bot_token']


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'tm_id', 'chat_id', 'username', 'contact']
    list_filter = ['faith_status']
    # readonly_fields = ['tm_id', 'chat_id']


@admin.register(models.MainMenu)
class MainMenuAdmin(admin.ModelAdmin):
    list_display = ['order', 'interface_name', 'button_name', 'city']
    list_display_links = ['order', 'interface_name',]
    list_filter = ['city']


@admin.register(models.SubCategories)
class SubCategoriesAdmin(admin.ModelAdmin):
    list_display = ['order', 'parent_category', 'manager', 'interface_name',]
    list_display_links = ['order', 'interface_name',]
    list_filter = ['parent_category__city', 'manager']


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['account', 'category', 'request_status']
    list_display_links = ['account']
    list_filter = ['request_status', 'category']
    readonly_fields = ['account', 'category', 'last_msg_id', 'last_message', 'date_create', 'request_status']
