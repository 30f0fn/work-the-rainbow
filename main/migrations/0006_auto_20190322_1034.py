# Generated by Django 2.1.5 on 2019-03-22 10:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_careday_classroom'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shiftassignment',
            old_name='family',
            new_name='child',
        ),
        migrations.RenameField(
            model_name='shiftpreference',
            old_name='family',
            new_name='child',
        ),
        migrations.RenameField(
            model_name='worktimecommitment',
            old_name='family',
            new_name='child',
        ),
    ]
