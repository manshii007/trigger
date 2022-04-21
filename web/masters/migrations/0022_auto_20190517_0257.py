# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-17 02:57
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0050_auto_20190313_1411'),
        ('masters', '0021_auto_20190516_2200'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorReportCommercial',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('duration', models.IntegerField()),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tags.Channel')),
                ('commercial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.VendorCommercial')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.Vendor')),
            ],
            options={
                'permissions': (('view_vendorreportcommercial', 'Can view vendor report commercial'),),
            },
        ),
        migrations.CreateModel(
            name='VendorReportProgram',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('duration', models.IntegerField()),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tags.Channel')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.VendorProgram')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.Vendor')),
            ],
            options={
                'permissions': (('view_vendorreportprogram', 'Can view vendor report program'),),
            },
        ),
        migrations.CreateModel(
            name='VendorReportPromo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('duration', models.IntegerField()),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tags.Channel')),
            ],
            options={
                'permissions': (('view_vendorreportpromo', 'Can view vendor report promo'),),
            },
        ),
        migrations.AddField(
            model_name='vendorpromo',
            name='durations',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(blank=True), null=True, size=12),
        ),
        migrations.AddField(
            model_name='vendorreportpromo',
            name='promo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.VendorPromo'),
        ),
        migrations.AddField(
            model_name='vendorreportpromo',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.Vendor'),
        ),
    ]