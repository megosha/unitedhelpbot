from django.contrib import admin

from tmbot import models




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
    list_display = ['name', 'tm_id', 'chat_id', 'contact']
    list_filter = ['faith_status', 'cities']
    #readonly_fields = ['tm_id', 'chat_id', 'faith_status',]


@admin.register(models.MainMenu)
class MainMenuAdmin(admin.ModelAdmin):
    list_display = ['order', 'interface_name', 'button_name', 'city']
    list_display_links = ['order', 'interface_name',]
    list_filter = ['city']


@admin.register(models.SubCategories)
class SubCategoriesAdmin(admin.ModelAdmin):
    list_display = ['order', 'interface_name', 'button_name', 'parent_category', 'manager']
    list_display_links = ['order', 'interface_name',]
    list_filter = ['parent_category__city', 'parent_category__interface_name']


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = 'pk', 'date_create', 'account', 'subcategory', 'request_status',
    list_display_links = 'pk', 'date_create', 'account',
    list_filter = 'subcategory__parent_category__city','request_status', 'subcategory',
    # readonly_fields = 'account', 'last_msg_id', 'subcategory', 'last_message', 'date_create', 'request_status'
