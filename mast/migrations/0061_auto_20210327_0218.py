# Generated by Django 3.1.7 on 2021-03-27 06:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mast', '0060_auto_20210327_0203'),
    ]

    operations = [
        migrations.AddField(
            model_name='director',
            name='department',
            field=models.CharField(default='DEF', max_length=3),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='student',
            name='major',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mast.major'),
        ),
        migrations.AddField(
            model_name='tracks_in_major',
            name='major',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='mast.major'),
            preserve_default=False,
        ),
    ]
