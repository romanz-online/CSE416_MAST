# Generated by Django 3.1.7 on 2021-04-05 03:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mast', '0003_trackcourseset_parent_course_set'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseintrackset',
            name='how_many_semesters',
            field=models.IntegerField(default=1),
        ),
    ]
