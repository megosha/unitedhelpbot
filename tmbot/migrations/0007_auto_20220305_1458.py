# Generated by Django 3.2.6 on 2022-03-05 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tmbot', '0006_auto_20220305_1301'),
    ]

    operations = [
        migrations.AddField(
            model_name='mainmenu',
            name='type',
            field=models.CharField(blank=True, choices=[('consult', 'Ручная'), ('automatic', 'Автоматическая')], max_length=20, null=True, verbose_name='Тип обработки'),
        ),
        migrations.AddField(
            model_name='subcategories',
            name='type',
            field=models.CharField(choices=[('consult', 'Ручная'), ('automatic', 'Автоматическая')], default='consult', max_length=20, verbose_name='Тип обработки'),
        ),
        migrations.AlterField(
            model_name='account',
            name='faith_status',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Неизвестно'), (1, 'Хожу в церковь Благословение'), (2, 'Хожу в другую церковь'), (3, 'Не хожу в церковь, в Бога верю'), (4, 'Не верю в Бога'), (5, 'Нет моего варианта')], default=0, verbose_name='Отношение к вере'),
        ),
    ]
