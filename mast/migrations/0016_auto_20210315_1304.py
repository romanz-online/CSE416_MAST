# Generated by Django 3.1.7 on 2021-03-15 17:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mast', '0015_auto_20210315_1303'),
    ]

    operations = [
        migrations.RenameField(
            model_name='classes_taken_by_student',
            old_name='in_progress',
            new_name='status',
        ),
    ]
