# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-05-08 09:14
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0034_auto_20180420_0459'),
    ]

    operations = [
        migrations.AddField(
            model_name='trivia',
            name='approved_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='approved_trivia', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='trivia',
            name='disapproved_reason',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='trivia',
            name='is_approved',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='trivia',
            name='source',
            field=models.URLField(null=True),
        ),
        migrations.AlterField(
            model_name='trivia',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='added_trivia', to=settings.AUTH_USER_MODEL),
        ),
    ]
