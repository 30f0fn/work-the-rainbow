# Generated by Django 2.1.5 on 2019-05-16 18:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0010_auto_20190420_1337'),
        ('main', '0014_shiftassignment_rank'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommitmentChangeNotice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_date', models.DateField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('_shift', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='main.Shift')),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Child')),
            ],
            options={
                'ordering': ('_date', '_shift'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CommitmentCreation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_date', models.DateField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('_shift', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='main.Shift')),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Child')),
            ],
            options={
                'ordering': ('_date', '_shift'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CommitmentDeletion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_date', models.DateField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('_shift', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='main.Shift')),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Child')),
            ],
            options={
                'ordering': ('_date', '_shift'),
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='worktimecommitment',
            options={},
        ),
        migrations.AlterUniqueTogether(
            name='worktimecommitment',
            unique_together={('shift', 'start')},
        ),
    ]