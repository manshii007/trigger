# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-03-09 17:18
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0114_songasset_channel'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workflowtransitionhistory',
            name='asset_version',
        ),
        migrations.RemoveField(
            model_name='workflowtransitionhistory',
            name='work_flow',
        ),
        migrations.AddField(
            model_name='assetversion',
            name='proxy_type',
            field=models.CharField(blank=True, choices=[('MTR', 'Master'), ('ITM', 'Intermediate'), ('FIN', 'Final')], default='MTR', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='workflowtransitionhistory',
            name='work_flow_instance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='content.WorkFlowInstance'),
        ),
        migrations.AlterField(
            model_name='workflowinstancestep',
            name='work_flow_instance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='work_flow_instance_step', to='content.WorkFlowInstance'),
        ),
        migrations.AlterField(
            model_name='workflowstep',
            name='allowed_status',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('NS', 'Not Started'), ('REV', 'Review'), ('APR', 'Approve'), ('REJ', 'Reject'), ('RJE', 'Reject with Edits'), ('CMP', 'Completed'), ('FAI', 'Failed'), ('OK', 'Ok')], max_length=100), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='workflowtransitionhistory',
            name='transition_from',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transition_from', to='content.WorkFlowInstanceStep'),
        ),
        migrations.AlterField(
            model_name='workflowtransitionhistory',
            name='transition_to',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transition_to', to='content.WorkFlowInstanceStep'),
        ),
    ]
