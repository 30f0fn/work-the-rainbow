# Generated by Django 2.1.5 on 2019-03-17 19:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0002_auto_20190317_1914'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='_active_role',
            new_name='active_role',
        ),
    ]
