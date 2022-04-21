# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2021-06-14 13:44
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0068_video_picture'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tags', '0101_auto_20210608_0747'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckTag',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('frame_in', models.PositiveIntegerField()),
                ('frame_out', models.PositiveIntegerField()),
                ('height', models.FloatField(blank=True, default=0)),
                ('width', models.FloatField(blank=True, default=0)),
                ('up_left_x', models.FloatField(blank=True, default=0)),
                ('up_left_y', models.FloatField(blank=True, default=0)),
                ('img_width', models.FloatField(blank=True, default=0)),
                ('img_height', models.FloatField(blank=True, default=0)),
                ('image_url', models.URLField(verbose_name='Image URL')),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('autotag', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='autotag', to='tags.GenericTag')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('usertag', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='usertag', to='tags.GenericTag')),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checktag', to='video.Video')),
            ],
            options={
                'permissions': (('view_checktag', 'Can view check tags'),),
            },
        ),
    ]
