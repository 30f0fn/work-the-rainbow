# Generated by Django 2.1.5 on 2019-04-06 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_remove_period_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='period',
            name='solicits_preferences',
            field=models.BooleanField(default=True),
        ),
    ]