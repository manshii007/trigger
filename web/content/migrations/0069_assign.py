# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-10-02 08:51
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0017_subtitle_version'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0068_remove_collection_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assign',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('collection', models.ManyToManyField(blank=True, null=True, to='content.Collection')),
                ('episode', models.ManyToManyField(blank=True, null=True, to='content.Episode')),
                ('movie', models.ManyToManyField(blank=True, null=True, to='content.Movie')),
                ('series', models.ManyToManyField(blank=True, null=True, to='content.Series')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('video', models.ManyToManyField(blank=True, null=True, to='video.Video')),
            ],
            options={
                'permissions': (('Assign', 'Assign to user'),),
            },
        ),
    ]
