# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-16 08:27
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0123_auto_20200415_1215'),
    ]

    operations = [
        migrations.CreateModel(
            name='Commercial',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=128, null=True)),
                ('aka_title', models.CharField(blank=True, max_length=256, null=True)),
                ('house_number', models.CharField(blank=True, max_length=128, null=True)),
                ('product_code', models.CharField(blank=True, max_length=256, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('country_of_origin', models.CharField(blank=True, max_length=128, null=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='added_commercial', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': (('view_commercial', 'Can view commercial'),),
            },
        ),
        migrations.AddField(
            model_name='assetversion',
            name='aka_title',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='album',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='aspect_ratio',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='audio_avaialble',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='audio_languages',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='audio_tracks',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='barcode',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='bitrate',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='certification',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='classification',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='codec',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='compliance_status',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='country_of_origin',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='created_for_month_year',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='dublist_export_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='duration',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='estimated_first_air_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='event_type',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='expiry_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='format_type',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='frame_rate',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='height',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='house_number',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='keywords',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='language',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='priority',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='producers',
            field=models.ManyToManyField(blank=True, related_name='assetversion_producer', to='content.Person'),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='product_code',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='production_house',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='production_number',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='size',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='slot_duration',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='status',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='subtitle_avaialble',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='subtitle_languages',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='total_frames',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='tx_id',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='tx_run_time',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='version_title',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='assetversion',
            name='width',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
