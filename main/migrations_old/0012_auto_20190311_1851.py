# Generated by Django 2.1.5 on 2019-03-11 18:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_auto_20190311_1800'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='caredayassignment',
            options={},
        ),
        migrations.RemoveField(
            model_name='caredayassignment',
            name='end_time',
        ),
        migrations.RemoveField(
            model_name='caredayassignment',
            name='start_time',
        ),
        migrations.RemoveField(
            model_name='caredayassignment',
            name='weekday',
        ),
    ]