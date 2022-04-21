# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-01-16 10:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0005_auto_20170112_1707'),
    ]

    operations = [
        migrations.AlterField(
            model_name='frametag',
            name='tag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='frametag', to='tags.Tag'),
        ),
        migrations.AlterField(
            model_name='frametag',
            name='video',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='frametag', to='video.Video'),
        ),
    ]