# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-15 07:27
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0121_auto_20200401_0723'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='song',
            name='length',
        ),
        migrations.RemoveField(
            model_name='song',
            name='recorded_in',
        ),
        migrations.AddField(
            model_name='song',
            name='aka_title',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='album',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='barcode',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='certification',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='classification',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='country_of_origin',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='added_song', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='song',
            name='external_ref_number',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='keywords',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='makers',
            field=models.ManyToManyField(blank=True, related_name='songs_makers', to='content.Person'),
        ),
        migrations.AddField(
            model_name='song',
            name='prod_year',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='production',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='production_house',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='role',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='slot_duration',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='song_id',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='status',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='tx_id',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='tx_run_time',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
