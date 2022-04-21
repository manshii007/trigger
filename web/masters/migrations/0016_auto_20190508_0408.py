# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-08 04:08
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0050_auto_20190313_1411'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('masters', '0015_auto_20190508_0401'),
    ]

    operations = [
        migrations.CreateModel(
            name='Advertiser',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AdvertiserGroup',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BrandCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BrandName',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('brand_category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.BrandCategory')),
            ],
        ),
        migrations.CreateModel(
            name='BrandSector',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ContentLanguage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Descriptor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('text', models.CharField(max_length=128)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductionHouse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProgramGenre',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProgramTheme',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PromoCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PromoType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('abbr', models.CharField(max_length=5)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SuperCommercial',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('advertiser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.Advertiser')),
                ('brand_name', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.BrandName')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('descriptor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.Descriptor')),
            ],
        ),
        migrations.CreateModel(
            name='SuperProgram',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tags.Channel')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('language', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.ContentLanguage')),
                ('prod_house', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.ProductionHouse')),
                ('program_genre', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.ProgramGenre')),
            ],
        ),
        migrations.CreateModel(
            name='SuperPromo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('advertiser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.Advertiser')),
                ('brand_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.BrandName')),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='broadcasted_super_promo', to='tags.Channel')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('descriptor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.Descriptor')),
                ('promo_channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='super_promo', to='tags.Channel')),
            ],
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, null=True)),
                ('name', models.CharField(max_length=128)),
                ('code', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='superpromo',
            name='title',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.Title'),
        ),
        migrations.AddField(
            model_name='superprogram',
            name='title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.Title'),
        ),
        migrations.AddField(
            model_name='supercommercial',
            name='title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.Title'),
        ),
        migrations.AddField(
            model_name='programgenre',
            name='program_theme',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.ProgramTheme'),
        ),
        migrations.AddField(
            model_name='brandcategory',
            name='brand_sector',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.BrandSector'),
        ),
        migrations.AddField(
            model_name='advertiser',
            name='advertiser_group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.AdvertiserGroup'),
        ),
        migrations.AddField(
            model_name='vendorcommercial',
            name='super_commercial',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.SuperCommercial'),
        ),
        migrations.AddField(
            model_name='vendorprogram',
            name='super_program',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.SuperProgram'),
        ),
        migrations.AddField(
            model_name='vendorpromo',
            name='super_promo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='masters.SuperPromo'),
        ),
    ]