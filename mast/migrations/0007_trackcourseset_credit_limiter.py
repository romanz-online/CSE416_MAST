# Generated by Django 3.1.7 on 2021-04-12 05:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mast', '0006_auto_20210412_0114'),
    ]

    operations = [
        migrations.AddField(
            model_name='trackcourseset',
            name='credit_limiter',
            field=models.BooleanField(default=False),
        ),
    ]
