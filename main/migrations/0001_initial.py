# Generated by Django 2.1.5 on 2019-03-16 11:45

import datetime
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import main.model_fields
import main.utilities


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('people', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CareDay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('weekday', main.model_fields.WeekdayField(choices=[('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday'), ('5', 'Saturday'), ('6', 'Sunday')], max_length=1)),
            ],
            options={
                'ordering': ['weekday', 'start_time'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CareDayAssignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(default=django.utils.timezone.now)),
                ('end', models.DateTimeField(default=main.utilities.in_a_week)),
                ('careday', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.CareDay')),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Child')),
            ],
        ),
        migrations.CreateModel(
            name='ClassroomShiftSchedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Classroom')),
            ],
        ),
        migrations.CreateModel(
            name='ExtraCareDay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(default=django.utils.timezone.now)),
                ('end', models.DateTimeField(default=django.utils.timezone.now)),
                ('extended', models.BooleanField(default=False)),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Child')),
            ],
            options={
                'ordering': ['start', 'end'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Happening',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(default=django.utils.timezone.now)),
                ('end', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
            ],
            options={
                'ordering': ['start', 'end'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(default=django.utils.timezone.now)),
                ('end', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'ordering': ['start', 'end'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(default=django.utils.timezone.now)),
                ('end', models.DateTimeField(default=django.utils.timezone.now)),
                ('duration', models.DurationField(default=datetime.timedelta(days=112))),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Classroom')),
            ],
            options={
                'ordering': ['start', 'end'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('weekday', main.model_fields.WeekdayField(choices=[('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday'), ('5', 'Saturday'), ('6', 'Sunday')], max_length=1)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Classroom')),
            ],
            options={
                'ordering': ['weekday', 'start_time'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShiftAssignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Child')),
                ('period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Period')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Shift')),
            ],
        ),
        migrations.CreateModel(
            name='ShiftPreference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.IntegerField(choices=[(1, 'best'), (2, 'pretty good'), (3, 'acceptable')], default=3)),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Child')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Shift')),
            ],
        ),
        migrations.CreateModel(
            name='WorktimeCommitment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(default=django.utils.timezone.now)),
                ('end', models.DateTimeField(default=django.utils.timezone.now)),
                ('completed', models.NullBooleanField()),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Child')),
            ],
            options={
                'ordering': ['start', 'end'],
                'abstract': False,
            },
        ),
    ]
