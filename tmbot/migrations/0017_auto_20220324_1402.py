# Generated by Django 3.2.6 on 2022-03-24 14:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tmbot', '0016_auto_20220324_1346'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mainmenu',
            options={'ordering': ['order'], 'verbose_name': 'Главное меню', 'verbose_name_plural': 'Главное меню'},
        ),
        migrations.AlterModelOptions(
            name='subcategories',
            options={'ordering': ['order'], 'verbose_name': 'Подпункт меню', 'verbose_name_plural': 'Подпункты меню'},
        ),
    ]
