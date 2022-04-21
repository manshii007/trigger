# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-05-24 10:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0015_ocrtag_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='frametag',
            name='tag',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='frametag', to='tags.Tag'),
        ),
    ]