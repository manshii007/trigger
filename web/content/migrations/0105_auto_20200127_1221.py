# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-27 12:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0104_auto_20200125_1322'),
    ]

    operations = [
        migrations.RenameField(
            model_name='episode',
            old_name='content_synopsis',
            new_name='synopsis',
        ),
        migrations.RenameField(
            model_name='season',
            old_name='content_synopsis',
            new_name='synopsis',
        ),
        migrations.RemoveField(
            model_name='episode',
            name='genre',
        ),
        migrations.RemoveField(
            model_name='season',
            name='genre',
        ),
        migrations.RemoveField(
            model_name='series',
            name='cast',
        ),
        migrations.AddField(
            model_name='episode',
            name='actors',
            field=models.ManyToManyField(blank=True, related_name='episode_actors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='episode',
            name='directors',
            field=models.ManyToManyField(blank=True, related_name='episode_directors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='episode',
            name='dop',
            field=models.ManyToManyField(blank=True, related_name='episode_dop', to='content.Person'),
        ),
        migrations.AddField(
            model_name='episode',
            name='producers',
            field=models.ManyToManyField(blank=True, related_name='episode_producer', to='content.Person'),
        ),
        migrations.AddField(
            model_name='episode',
            name='screenplay',
            field=models.ManyToManyField(blank=True, related_name='episode_screenplay', to='content.Person'),
        ),
        migrations.AddField(
            model_name='season',
            name='actors',
            field=models.ManyToManyField(blank=True, related_name='season_actors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='season',
            name='directors',
            field=models.ManyToManyField(blank=True, related_name='season_directors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='season',
            name='dop',
            field=models.ManyToManyField(blank=True, related_name='season_dop', to='content.Person'),
        ),
        migrations.AddField(
            model_name='season',
            name='producers',
            field=models.ManyToManyField(blank=True, related_name='season_producer', to='content.Person'),
        ),
        migrations.AddField(
            model_name='series',
            name='actors',
            field=models.ManyToManyField(blank=True, related_name='series_actors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='series',
            name='directors',
            field=models.ManyToManyField(blank=True, related_name='series_directors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='series',
            name='dop',
            field=models.ManyToManyField(blank=True, related_name='series_dop', to='content.Person'),
        ),
        migrations.AddField(
            model_name='series',
            name='producers',
            field=models.ManyToManyField(blank=True, related_name='series_producer', to='content.Person'),
        ),
    ]
