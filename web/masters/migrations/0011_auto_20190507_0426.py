# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-07 04:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0050_auto_20190313_1411'),
        ('masters', '0010_vendorcommercial_durations'),
    ]

    operations = [
        migrations.CreateModel(
            name='Advertiser',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AdvertiserGroup',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BrandCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(blank=True, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BrandName',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(blank=True, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('brand_category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.BrandCategory')),
            ],
        ),
        migrations.CreateModel(
            name='BrandSector',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ContentLanguage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Descriptor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('text', models.CharField(max_length=128)),
                ('code', models.IntegerField(blank=True, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductionHouse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProgramGenre',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProgramTheme',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(null=True, unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PromoCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PromoType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('code', models.IntegerField(blank=True, null=True)),
                ('abbr', models.CharField(max_length=5)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('code', models.IntegerField(blank=True, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='advertiser_code',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='advertiser_group',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='advertiser_group_code',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='brand_category',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='brand_category_code',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='brand_name_code',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='brand_sector',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='brand_sector_code',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='descriptor_code',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='is_mapped',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='super_promo',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='title_code',
        ),
        migrations.RemoveField(
            model_name='superpromo',
            name='vendor',
        ),
        migrations.AddField(
            model_name='superpromo',
            name='channel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='broadcasted_super_promo', to='tags.Channel'),
        ),
        migrations.AddField(
            model_name='superpromo',
            name='promo_channel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='super_promo', to='tags.Channel'),
        ),
        migrations.AlterField(
            model_name='supercommercial',
            name='advertiser',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.Advertiser'),
        ),
        migrations.AlterField(
            model_name='supercommercial',
            name='brand_name',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.BrandName'),
        ),
        migrations.AlterField(
            model_name='supercommercial',
            name='descriptor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.Descriptor'),
        ),
        migrations.AlterField(
            model_name='supercommercial',
            name='title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.Title'),
        ),
        migrations.AlterField(
            model_name='superprogram',
            name='channel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tags.Channel'),
        ),
        migrations.AlterField(
            model_name='superprogram',
            name='language',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.ContentLanguage'),
        ),
        migrations.AlterField(
            model_name='superprogram',
            name='prod_house',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.ProductionHouse'),
        ),
        migrations.AlterField(
            model_name='superprogram',
            name='program_genre',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.ProgramGenre'),
        ),
        migrations.AlterField(
            model_name='superprogram',
            name='title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.Title'),
        ),
        migrations.AlterField(
            model_name='superpromo',
            name='advertiser',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.Advertiser'),
        ),
        migrations.AlterField(
            model_name='superpromo',
            name='brand_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='masters.BrandName'),
        ),
        migrations.AlterField(
            model_name='superpromo',
            name='descriptor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.Descriptor'),
        ),
        migrations.AlterField(
            model_name='superpromo',
            name='title',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.Title'),
        ),
        migrations.AlterField(
            model_name='vendorcommercial',
            name='super_commercial',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.SuperCommercial'),
        ),
        migrations.AlterField(
            model_name='vendorprogram',
            name='super_program',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.SuperProgram'),
        ),
        migrations.AlterField(
            model_name='vendorpromo',
            name='super_promo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='masters.SuperPromo'),
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
        migrations.RemoveField(
            model_name='supercommercial',
            name='advertiser_code',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='advertiser_group',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='advertiser_group_code',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='brand_category',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='brand_category_code',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='brand_name_code',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='brand_sector',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='brand_sector_code',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='descriptor_code',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='is_mapped',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='super_commercial',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='title_code',
        ),
        migrations.RemoveField(
            model_name='supercommercial',
            name='vendor',
        ),
        migrations.AlterUniqueTogether(
            name='supercommercial',
            unique_together=set([('brand_name', 'descriptor')]),
        ),
        migrations.RemoveField(
            model_name='superprogram',
            name='is_mapped',
        ),
        migrations.RemoveField(
            model_name='superprogram',
            name='language_code',
        ),
        migrations.RemoveField(
            model_name='superprogram',
            name='prod_house_code',
        ),
        migrations.RemoveField(
            model_name='superprogram',
            name='program_genre_code',
        ),
        migrations.RemoveField(
            model_name='superprogram',
            name='program_theme',
        ),
        migrations.RemoveField(
            model_name='superprogram',
            name='program_theme_code',
        ),
        migrations.RemoveField(
            model_name='superprogram',
            name='super_program',
        ),
        migrations.RemoveField(
            model_name='superprogram',
            name='title_code',
        ),
        migrations.RemoveField(
            model_name='superprogram',
            name='vendor',
        ),
        migrations.AlterUniqueTogether(
            name='superprogram',
            unique_together=set([('title', 'channel')]),
        ),
    ]
