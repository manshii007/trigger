# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-03-09 08:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0044_auto_20190309_0845'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brandname',
            name='brand_category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.BrandCategory'),
        ),
        migrations.AlterField(
            model_name='brandname',
            name='code',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='commercial',
            name='brand_name',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.BrandName'),
        ),
    ]
