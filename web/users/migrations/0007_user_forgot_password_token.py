# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2022-03-07 06:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20171208_0707'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='forgot_password_token',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_demo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='recent_search',
            field=models.TextField(null=True),
        ),
    ]
