# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-02-05 11:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0038_auto_20200205_0802'),
    ]

    operations = [
        migrations.CreateModel(
            name='Clip',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('clip_ref', models.UUIDField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('ticket_ref', models.UUIDField(blank=True, null=True)),
                ('project', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='videoproxypath',
            name='sourceproxy_upload_status',
            field=models.CharField(blank=True, choices=[('UPL', 'Uploading'), ('NST', 'Uploading not Started'), ('UPD', 'Sucessfully Uploaded'), ('FAI', 'Uploading Failed')], default='NST', max_length=3, null=True),
        ),
        migrations.AddField(
            model_name='clip',
            name='ticket',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='video.Ticket'),
        ),
        migrations.AddField(
            model_name='clip',
            name='video_proxy_path',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='video.VideoProxyPath'),
        ),
    ]
