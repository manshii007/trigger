# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-05-01 06:09
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0065_auto_20200501_0550'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='video',
            name='metadata',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='video.VideoProxyPath'),
        ),
    ]