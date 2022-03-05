# Generated by Django 3.2.6 on 2022-03-05 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tmbot', '0003_auto_20220304_1821'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='user',
        ),
        migrations.AddField(
            model_name='account',
            name='name',
            field=models.CharField(default='', max_length=50, verbose_name='Имя пользователя'),
        ),
    ]
