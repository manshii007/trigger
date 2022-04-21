# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-12-24 08:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0081_auto_20191224_0803'),
    ]

    operations = [
        migrations.AlterField(
            model_name='frametag',
            name='video',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='video', to='video.Video'),
        ),
    ]
