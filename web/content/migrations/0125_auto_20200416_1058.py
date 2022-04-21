# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-16 10:58
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0124_auto_20200416_0827'),
    ]

    operations = [
        migrations.AddField(
            model_name='songasset',
            name='aka_title',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='album',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='barcode',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='certification',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='classification',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='country_of_origin',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_songasset', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='songasset',
            name='external_ref_number',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='keywords',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='makers',
            field=models.ManyToManyField(blank=True, related_name='songsasset_makers', to='content.Person'),
        ),
        migrations.AddField(
            model_name='songasset',
            name='movie',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.Movie'),
        ),
        migrations.AddField(
            model_name='songasset',
            name='music_directors',
            field=models.ManyToManyField(blank=True, related_name='songsasset_ms_director', to='content.Person'),
        ),
        migrations.AddField(
            model_name='songasset',
            name='prod_year',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='production',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='production_house',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='role',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='slot_duration',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='song_id',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='status',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='tx_id',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='tx_run_time',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='movie',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_movie', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='promo',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_promo', to=settings.AUTH_USER_MODEL),
        ),
    ]