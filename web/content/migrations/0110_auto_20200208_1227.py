# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-02-08 12:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0109_auto_20200208_0936'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkFlowInstanceStep',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('work_flow_step_status', models.CharField(blank=True, max_length=100, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'permissions': (('view_workflowinstancestep', 'Can view WorkFlowInstanceStep'),),
            },
        ),
        migrations.RemoveField(
            model_name='workflowinstance',
            name='work_flow_step',
        ),
        migrations.RemoveField(
            model_name='workflowinstance',
            name='work_flow_step_status',
        ),
        migrations.AddField(
            model_name='workflowinstancestep',
            name='work_flow_instance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='content.WorkFlowInstance'),
        ),
        migrations.AddField(
            model_name='workflowinstancestep',
            name='work_flow_step',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='content.WorkFlowStep'),
        ),
        migrations.AlterUniqueTogether(
            name='workflowinstancestep',
            unique_together=set([('work_flow_instance', 'work_flow_step')]),
        ),
    ]