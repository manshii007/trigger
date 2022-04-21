# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-10-03 08:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('content', '0069_assign'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assign',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='assign',
            name='episode',
        ),
        migrations.RemoveField(
            model_name='assign',
            name='movie',
        ),
        migrations.RemoveField(
            model_name='assign',
            name='series',
        ),
        migrations.RemoveField(
            model_name='assign',
            name='video',
        ),
        migrations.AddField(
            model_name='assign',
            name='content_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='assign',
            name='object_id',
            field=models.UUIDField(blank=True, null=True),
        ),
    ]
