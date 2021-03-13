# Generated by Django 3.1.7 on 2021-03-13 01:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sbu_id', models.IntegerField()),
                ('name', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=100)),
                ('graduated', models.BooleanField(default=False)),
                ('withdrew', models.BooleanField(default=False)),
                ('password', models.CharField(max_length=100)),
            ],
        ),
    ]
