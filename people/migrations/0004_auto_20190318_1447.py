# Generated by Django 2.1.5 on 2019-03-18 14:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0003_auto_20190317_1931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='child',
            name='classroom',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='people.Classroom'),
        ),
    ]
