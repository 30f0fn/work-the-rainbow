# Generated by Django 2.1.5 on 2019-02-18 22:17

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0004_auto_20190207_0304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classroom',
            name='scheduler_set',
            field=models.ManyToManyField(related_name='_classrooms_as_scheduler', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='classroom',
            name='teacher_set',
            field=models.ManyToManyField(related_name='_classrooms_as_teacher', to=settings.AUTH_USER_MODEL),
        ),
    ]
