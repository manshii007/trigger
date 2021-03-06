# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-06 06:07
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tags', '0050_auto_20190313_1411'),
        ('masters', '0008_auto_20190506_0458'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuperCommercial',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=128)),
                ('title_code', models.CharField(max_length=128)),
                ('brand_name', models.CharField(max_length=128)),
                ('brand_name_code', models.CharField(max_length=128)),
                ('brand_sector', models.CharField(max_length=128)),
                ('brand_sector_code', models.CharField(max_length=128)),
                ('brand_category', models.CharField(max_length=128)),
                ('brand_category_code', models.CharField(max_length=128)),
                ('advertiser', models.CharField(max_length=128)),
                ('advertiser_code', models.CharField(max_length=128)),
                ('advertiser_group', models.CharField(max_length=128)),
                ('advertiser_group_code', models.CharField(max_length=128)),
                ('descriptor', models.CharField(max_length=128)),
                ('descriptor_code', models.CharField(max_length=128)),
                ('is_mapped', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('super_commercial', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.Commercial')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.Vendor')),
            ],
        ),
        migrations.CreateModel(
            name='SuperProgram',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=128, null=True)),
                ('title_code', models.CharField(max_length=128, null=True)),
                ('language', models.CharField(max_length=128, null=True)),
                ('language_code', models.CharField(max_length=128, null=True)),
                ('prod_house', models.CharField(max_length=128, null=True)),
                ('prod_house_code', models.CharField(max_length=128, null=True)),
                ('program_genre', models.CharField(max_length=128, null=True)),
                ('program_genre_code', models.CharField(max_length=128, null=True)),
                ('program_theme', models.CharField(max_length=128, null=True)),
                ('program_theme_code', models.CharField(max_length=128, null=True)),
                ('is_mapped', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.Channel')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('super_program', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.Program')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.Vendor')),
            ],
        ),
        migrations.CreateModel(
            name='SuperPromo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=128)),
                ('title_code', models.CharField(max_length=128)),
                ('brand_name', models.CharField(max_length=128)),
                ('brand_name_code', models.CharField(max_length=128)),
                ('brand_sector', models.CharField(max_length=128)),
                ('brand_sector_code', models.CharField(max_length=128)),
                ('brand_category', models.CharField(max_length=128)),
                ('brand_category_code', models.CharField(max_length=128)),
                ('advertiser', models.CharField(max_length=128, null=True)),
                ('advertiser_code', models.CharField(max_length=128, null=True)),
                ('advertiser_group', models.CharField(max_length=128, null=True)),
                ('advertiser_group_code', models.CharField(max_length=128, null=True)),
                ('descriptor', models.CharField(max_length=128, null=True)),
                ('descriptor_code', models.CharField(max_length=128, null=True)),
                ('is_mapped', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('super_promo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.Promo')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.Vendor')),
            ],
        ),
    ]
