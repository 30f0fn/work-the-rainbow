# Generated by Django 2.1.5 on 2019-04-03 19:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_auto_20190322_1034'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='caredayassignment',
            options={'ordering': ['careday', 'start', 'end']},
        ),
    ]
