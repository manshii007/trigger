# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-05-14 15:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contextual', '0006_auto_20170514_1508'),
        ('frames', '0005_auto_20170514_1508'),
    ]

    operations = [
        migrations.AddField(
            model_name='picturegroup',
            name='frames',
            field=models.ManyToManyField(to='frames.PictureFrame'),
        ),
    ]