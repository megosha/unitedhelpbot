# Generated by Django 3.2.6 on 2022-03-11 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tmbot', '0009_auto_20220310_1736'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='website',
            field=models.TextField(blank=True, default='church22.ru', verbose_name='Текст с контактами'),
        ),
    ]
