# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-05-08 18:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contextual', '0003_auto_20170508_1044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='face',
            name='azureFaceId',
            field=models.CharField(max_length=128, verbose_name='Face Id'),
        ),
        migrations.AlterField(
            model_name='face',
            name='faceGroup',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contextual.FaceGroup', verbose_name='Face Group'),
        ),
        migrations.AlterField(
            model_name='face',
            name='faceImg',
            field=models.URLField(verbose_name='Image URL'),
        ),
        migrations.AlterField(
            model_name='face',
            name='faceRect',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='frames.FaceRect', verbose_name='Rect'),
        ),
    ]
