# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-11-30 07:37
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0013_tvanchor'),
    ]

    operations = [
        migrations.AddField(
            model_name='politician',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
