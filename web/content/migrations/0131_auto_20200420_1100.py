# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-20 11:00
from __future__ import unicode_literals

from django.db import migrations, models
import utils.unique_filename
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0130_auto_20200419_1233'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movie',
            name='cbfc',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='production',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='remark',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='secondary_title',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='secondary_title',
        ),
        migrations.RemoveField(
            model_name='song',
            name='production',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='length',
        ),
        migrations.RemoveField(
            model_name='songasset',
            name='recorded_in',
        ),
        migrations.AddField(
            model_name='commercial',
            name='poster',
            field=versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to=utils.unique_filename.unique_upload, verbose_name='Poster'),
        ),
        migrations.AddField(
            model_name='commercial',
            name='poster_ppoi',
            field=versatileimagefield.fields.PPOIField(default='0.5x0.5', editable=False, max_length=20),
        ),
        migrations.AddField(
            model_name='movie',
            name='part_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='rank',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='type_movie',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='promo',
            name='sequence',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='promo',
            name='timecode_in',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='promo',
            name='unpackaged_master',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='duration',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='part_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='rank',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='songasset',
            name='type_song',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
