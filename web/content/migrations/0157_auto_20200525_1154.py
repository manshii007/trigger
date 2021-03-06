# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-05-25 11:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0099_auto_20200525_1127'),
        ('content', '0156_auto_20200525_1147'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commercialasset',
            name='house_number',
        ),
        migrations.AddField(
            model_name='commercialasset',
            name='production_house',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.ProductionHouse'),
        ),
        migrations.AddField(
            model_name='movie',
            name='production_house',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.ProductionHouse'),
        ),
        migrations.AddField(
            model_name='songasset',
            name='production_house',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tags.ProductionHouse'),
        ),
    ]
