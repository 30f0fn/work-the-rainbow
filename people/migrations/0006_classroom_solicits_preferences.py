# Generated by Django 2.1.5 on 2019-04-03 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0005_auto_20190322_1034'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroom',
            name='solicits_preferences',
            field=models.BooleanField(default=True),
        ),
    ]