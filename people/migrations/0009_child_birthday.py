# Generated by Django 2.1.5 on 2019-04-14 00:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0008_child_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='child',
            name='birthday',
            field=models.DateField(blank=True, null=True),
        ),
    ]
