# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-25 13:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0103_auto_20200125_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='season',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='episodes', to='content.Season'),
        ),
        migrations.AlterField(
            model_name='season',
            name='series',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seasons', to='content.Series'),
        ),
    ]