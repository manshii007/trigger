# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-16 11:13
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0125_auto_20200416_1058'),
    ]

    operations = [
        migrations.AddField(
            model_name='rushes',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_rushes', to=settings.AUTH_USER_MODEL),
        ),
    ]
