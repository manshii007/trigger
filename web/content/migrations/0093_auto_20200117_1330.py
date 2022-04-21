# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-01-17 13:30
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0092_videoprocessingstatus_processed'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rushes',
            old_name='content_synopsis',
            new_name='synopsis',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='cast',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='movie_directors',
        ),
        migrations.RemoveField(
            model_name='rushes',
            name='cast',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='duration',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='movie_directors',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='music_directors',
        ),
        migrations.AddField(
            model_name='promo',
            name='actors',
            field=models.ManyToManyField(blank=True, related_name='promo_actors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='promo',
            name='directors',
            field=models.ManyToManyField(blank=True, related_name='promo_directors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='promo',
            name='dop',
            field=models.ManyToManyField(blank=True, related_name='promo_dop', to='content.Person'),
        ),
        migrations.AddField(
            model_name='promo',
            name='location',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='promo',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='promo_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='promo',
            name='producers',
            field=models.ManyToManyField(blank=True, related_name='promo_producer', to='content.Person'),
        ),
        migrations.AddField(
            model_name='promo',
            name='screenplay',
            field=models.ManyToManyField(blank=True, related_name='promo_screenplay', to='content.Person'),
        ),
        migrations.AddField(
            model_name='promo',
            name='synopsis',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rushes',
            name='actors',
            field=models.ManyToManyField(blank=True, related_name='rushes_actors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='rushes',
            name='directors',
            field=models.ManyToManyField(blank=True, related_name='rushes_directors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='rushes',
            name='dop',
            field=models.ManyToManyField(blank=True, related_name='rushes_dop', to='content.Person'),
        ),
        migrations.AddField(
            model_name='rushes',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='rushes',
            name='producers',
            field=models.ManyToManyField(blank=True, related_name='rushes_producer', to='content.Person'),
        ),
        migrations.AddField(
            model_name='rushes',
            name='screenplay',
            field=models.ManyToManyField(blank=True, related_name='rushes_screenplay', to='content.Person'),
        ),
        migrations.AddField(
            model_name='songasset',
            name='directors',
            field=models.ManyToManyField(blank=True, related_name='songsasset_directors', to='content.Person'),
        ),
        migrations.AddField(
            model_name='songasset',
            name='dop',
            field=models.ManyToManyField(blank=True, related_name='songsasset_dop', to='content.Person'),
        ),
        migrations.AddField(
            model_name='songasset',
            name='location',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='songasset',
            name='screenplay',
            field=models.ManyToManyField(blank=True, related_name='songsasset_screenplay', to='content.Person'),
        ),
        migrations.AddField(
            model_name='songasset',
            name='synopsis',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='songasset',
            name='producers',
            field=models.ManyToManyField(blank=True, related_name='songsasset_producers', to='content.Person'),
        ),
        migrations.AlterField(
            model_name='songasset',
            name='song_writers',
            field=models.ManyToManyField(blank=True, related_name='songsasset_song_writers', to='content.Person'),
        ),
    ]
