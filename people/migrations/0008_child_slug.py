# Generated by Django 2.1.5 on 2019-04-14 00:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0007_remove_classroom_solicits_preferences'),
    ]

    operations = [
        migrations.AddField(
            model_name='child',
            name='slug',
            field=models.SlugField(null=True, unique=True),
        ),
    ]
