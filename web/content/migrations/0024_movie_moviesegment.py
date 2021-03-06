# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-03-04 06:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0014_videosubtitle'),
        ('content', '0023_remove_episode_keywords'),
    ]

    operations = [
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('movie_title', models.CharField(max_length=128)),
                ('secondary_title', models.CharField(blank=True, max_length=128)),
                ('short_title', models.CharField(blank=True, max_length=128)),
                ('year_of_release', models.DateField(blank=True, null=True)),
                ('language', models.TextField(blank=True, null=True)),
                ('content_subject', models.CharField(blank=True, max_length=128, null=True)),
                ('content_synopsis', models.TextField(blank=True, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='content.Channel')),
                ('characters', models.ManyToManyField(blank=True, to='content.Character')),
                ('genre', models.ManyToManyField(blank=True, to='content.Genre')),
            ],
        ),
        migrations.CreateModel(
            name='MovieSegment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='content.Movie')),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='video.Video')),
            ],
        ),
    ]
