# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-12-21 08:05
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0077_auto_20191108_0830'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignAssetVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'permissions': (('Assign', 'Assign to user'),),
            },
        ),
        migrations.CreateModel(
            name='WorkFlow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('description', models.CharField(blank=True, max_length=1024, null=True)),
                ('title', models.CharField(max_length=128)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='WorkFlowInstance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=128)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='WorkFlowStage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='WorkFlowStep',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('description', models.CharField(blank=True, max_length=1024, null=True)),
                ('title', models.CharField(max_length=128)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='WorkFlowTransitionHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('transition_from', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transition_from', to='content.WorkFlowStep')),
                ('transition_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transition_to', to='content.WorkFlowStep')),
                ('work_flow', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='content.WorkFlow')),
            ],
        ),
        migrations.RemoveField(
            model_name='assign',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='assign',
            name='user',
        ),
        migrations.RenameField(
            model_name='assetversion',
            old_name='name',
            new_name='title',
        ),
        migrations.RenameField(
            model_name='collection',
            old_name='name',
            new_name='title',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='video',
        ),
        migrations.AddField(
            model_name='collection',
            name='asset_version',
            field=models.ManyToManyField(blank=True, null=True, to='content.AssetVersion'),
        ),
        migrations.AddField(
            model_name='collection',
            name='channel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.Channel'),
        ),
        migrations.AddField(
            model_name='collection',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='person',
            name='charatcer_played',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=200), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='promo',
            name='channel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.Channel'),
        ),
        migrations.AddField(
            model_name='promo',
            name='genre',
            field=models.ManyToManyField(blank=True, to='content.Genre'),
        ),
        migrations.AddField(
            model_name='promo',
            name='movie',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.Movie'),
        ),
        migrations.AddField(
            model_name='promo',
            name='movie_directors',
            field=models.ManyToManyField(blank=True, related_name='promo_ms_director', to='content.Person'),
        ),
        migrations.AddField(
            model_name='promo',
            name='promo_number',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='promo',
            name='year_of_release',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rushes',
            name='event_location',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='rushes',
            name='event_name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='rushes',
            name='mood',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='duration',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='lyrics',
            field=models.CharField(blank=True, max_length=5000, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='movie_directors',
            field=models.ManyToManyField(blank=True, related_name='songs_movie_director', to='content.Person'),
        ),
        migrations.AddField(
            model_name='song',
            name='original_remake',
            field=models.CharField(blank=True, max_length=5000, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='tempo',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='song',
            name='version',
            field=models.CharField(blank=True, max_length=5000, null=True),
        ),
        migrations.DeleteModel(
            name='Assign',
        ),
        migrations.AddField(
            model_name='workflowstage',
            name='next_step',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='next_step', to='content.WorkFlowStep'),
        ),
        migrations.AddField(
            model_name='workflowstage',
            name='prev_step',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='previous_step', to='content.WorkFlowStep'),
        ),
        migrations.AddField(
            model_name='workflowstage',
            name='work_flow',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='content.WorkFlow'),
        ),
        migrations.AddField(
            model_name='workflowinstance',
            name='asset_version',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.AssetVersion'),
        ),
        migrations.AddField(
            model_name='workflowinstance',
            name='work_flow',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='content.WorkFlow'),
        ),
        migrations.AddField(
            model_name='workflowinstance',
            name='work_flow_step',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='content.WorkFlowStep'),
        ),
        migrations.AddField(
            model_name='assignassetversion',
            name='asset_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.AssetVersion'),
        ),
        migrations.AddField(
            model_name='assignassetversion',
            name='assigned_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='assignassetversion',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_to', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='collection',
            name='workflow',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.WorkFlow'),
        ),
        migrations.AlterUniqueTogether(
            name='assignassetversion',
            unique_together=set([('asset_version', 'assigned_to')]),
        ),
    ]