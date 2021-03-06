# Generated by Django 3.2.6 on 2022-03-24 13:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tmbot', '0015_alter_subcategories_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mainmenu',
            options={'ordering': ['pk'], 'verbose_name': 'Главное меню', 'verbose_name_plural': 'Главное меню'},
        ),
        migrations.AlterModelOptions(
            name='subcategories',
            options={'ordering': ['pk'], 'verbose_name': 'Подпункт меню', 'verbose_name_plural': 'Подпункты меню'},
        ),
        migrations.AlterUniqueTogether(
            name='subcategories',
            unique_together=set(),
        ),
    ]
