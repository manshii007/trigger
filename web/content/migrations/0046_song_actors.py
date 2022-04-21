# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-07-05 08:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0045_auto_20180704_0504'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='actors',
            field=models.ManyToManyField(related_name='songs_actors', to='content.Person'),
        ),
    ]