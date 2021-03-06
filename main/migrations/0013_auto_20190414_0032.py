# Generated by Django 2.1.5 on 2019-04-14 00:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_period_solicits_preferences'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='shiftpreference',
            options={'ordering': ('period', 'rank', 'shift')},
        ),
        migrations.AlterField(
            model_name='shiftpreference',
            name='rank',
            field=models.IntegerField(blank=True, choices=[(1, 'best'), (2, 'pretty good'), (3, 'acceptable')], default=3, null=True),
        ),
    ]
