# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-08 14:27
from __future__ import unicode_literals

from django.db import migrations
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0013_logo_logotag'),
    ]

    operations = [
        migrations.AddField(
            model_name='logo',
            name='poster_ppoi',
            field=versatileimagefield.fields.PPOIField(default='0.5x0.5', editable=False, max_length=20),
        ),
    ]
