# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-12 09:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0015_ocrtag_language'),
        ('content', '0028_trivia'),
    ]

    operations = [
        migrations.AddField(
            model_name='trivia',
            name='tags',
            field=models.ManyToManyField(to='tags.Tag'),
        ),
    ]
