# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-01-02 07:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0002_auto_20170101_0507'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.TagCategory'),
        ),
    ]