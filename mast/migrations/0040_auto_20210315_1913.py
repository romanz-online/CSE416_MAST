# Generated by Django 3.1.7 on 2021-03-15 23:13

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mast', '0039_auto_20210315_1909'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='post_date',
            field=models.CharField(default=datetime.datetime(2021, 3, 15, 19, 13, 40, 963849), max_length=100),
        ),
    ]
