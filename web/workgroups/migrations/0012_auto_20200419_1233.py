# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2020-04-19 12:33
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workgroups', '0011_auto_20200403_0949'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workgroupmembership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='membership', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, null=True, unique=True)),
                ('group', models.ManyToManyField(related_name='team_group', to='auth.Group')),
            ],
            options={
                'permissions': (('user_view_team', 'User level can view team'), ('team_view_team', 'Team level can view team'), ('org_view_team', 'Org level can view team'), ('user_add_team', 'User level can add team'), ('team_add_team', 'Team level can add team'), ('org_add_team', 'Org level can add team'), ('user_change_team', 'User level can change team'), ('team_change_team', 'Team level can change team'), ('org_change_team', 'Org level can change team'), ('user_delete_team', 'User level can delete team'), ('team_delete_team', 'Team level can delete team'), ('org_delete_team', 'Org level can delete team')),
            },
        ),
        migrations.AlterModelOptions(
            name='organization',
            options={'permissions': (('user_view_organization', 'User level can view organization'), ('team_view_organization', 'Team level can view organization'), ('org_view_organization', 'Org level can view organization'), ('user_add_organization', 'User level can add organization'), ('team_add_organization', 'Team level can add organization'), ('org_add_organization', 'Org level can add organization'), ('user_change_organization', 'User level can change organization'), ('team_change_organization', 'Team level can change organization'), ('org_change_organization', 'Org level can change organization'), ('user_delete_organization', 'User level can delete organization'), ('team_delete_organization', 'Team level can delete organization'), ('org_delete_organization', 'Org level can delete organization'))},
        ),
        migrations.RemoveField(
            model_name='workgroup',
            name='videolibrary',
        ),
        migrations.AddField(
            model_name='organization',
            name='group',
            field=models.ManyToManyField(related_name='org_group', to='auth.Group'),
        ),
        migrations.AddField(
            model_name='team',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='team_org', to='workgroups.Organization'),
        ),
        migrations.AddField(
            model_name='team',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='team',
            name='user',
            field=models.ManyToManyField(related_name='team_user', to=settings.AUTH_USER_MODEL),
        ),
    ]
