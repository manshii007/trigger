# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-05-08 07:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0096_auto_20200423_1618'),
        ('content', '0143_auto_20200508_0704'),
    ]

    operations = [
        migrations.AddField(
            model_name='assetversion',
            name='language',
            field=models.ManyToManyField(blank=True, related_name='assetversion_language', to='tags.ContentLanguage'),
        ),
        migrations.AddField(
            model_name='commercial',
            name='language',
            field=models.ManyToManyField(blank=True, related_name='commercial_language', to='tags.ContentLanguage'),
        ),
        migrations.AddField(
            model_name='movie',
            name='language',
            field=models.ManyToManyField(blank=True, related_name='movie_language', to='tags.ContentLanguage'),
        ),
        migrations.AddField(
            model_name='promo',
            name='language',
            field=models.ManyToManyField(blank=True, related_name='promo_language', to='tags.ContentLanguage'),
        ),
        migrations.AddField(
            model_name='rushes',
            name='language',
            field=models.ManyToManyField(blank=True, related_name='rushes_language', to='tags.ContentLanguage'),
        ),
        migrations.AddField(
            model_name='songasset',
            name='language',
            field=models.ManyToManyField(blank=True, related_name='songasset_language', to='tags.ContentLanguage'),
        ),
    ]
