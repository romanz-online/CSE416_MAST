# Generated by Django 3.1.7 on 2021-03-15 23:06

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mast', '0036_auto_20210315_1858'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='post_date',
            field=models.CharField(default=datetime.datetime(2021, 3, 15, 19, 6, 44, 2014), max_length=100),
        ),
        migrations.CreateModel(
            name='Tracks_in_Major',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('major', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mast.course')),
            ],
        ),
        migrations.AlterField(
            model_name='student',
            name='track',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mast.tracks_in_major'),
        ),
    ]
