#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import Group, Permission

import uuid

from video.models import (
    VideoLibrary
)
from users.models import User


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ManyToManyField(Group, null=False, related_name="org_group")
    name = models.CharField(max_length=128, unique=True, null=True)
    owner = models.ForeignKey(User, null=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (
            ("user_view_organization", "User level can view organization"),("team_view_organization", "Team level can view organization"), ("org_view_organization", "Org level can view organization"),
            ("user_add_organization", "User level can add organization"),("team_add_organization", "Team level can add organization"), ("org_add_organization", "Org level can add organization"),
            ("user_change_organization", "User level can change organization"),("team_change_organization", "Team level can change organization"), ("org_change_organization", "Org level can change organization"),
            ("user_delete_organization", "User level can delete organization"),("team_delete_organization", "Team level can delete organization"), ("org_delete_organization", "Org level can delete organization"),
        )


class WorkGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.OneToOneField(Group, primary_key=False, related_name='workgroup')
    name = models.CharField(max_length=128, unique=True, null=True, verbose_name='Workgroup Name')
    owner = models.ForeignKey(User, null=True)
    organization = models.ForeignKey(Organization, null=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (("view_workgroup", "Can view work group"),)


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=128, unique=True, null=True)
    description = models.CharField(max_length=1024, null=True, blank=True)
    permissions = models.ManyToManyField(Permission, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        permissions = (("view_role", "Can view role"),)


class WorkGroupMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, null=False, related_name="membership")
    workgroup = models.ForeignKey(WorkGroup, null=False, related_name="members")
    role = models.ManyToManyField(Role, null=False)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        permissions = (("view_workgroupmembership", "Can view work group membership"),)
        unique_together = ('user', 'workgroup',)

class Team(models.Model):
    user = models.ManyToManyField(User, null=False, related_name="team_user")
    group = models.ManyToManyField(Group, null=False, related_name="team_group")
    organization = models.ForeignKey(Organization, null=True, related_name="team_org")
    name = models.CharField(max_length=128, unique=True, null=True)
    owner = models.ForeignKey(User, null=True)

    class Meta:
        permissions = (
            ("user_view_team", "User level can view team"),("team_view_team", "Team level can view team"), ("org_view_team", "Org level can view team"),
            ("user_add_team", "User level can add team"),("team_add_team", "Team level can add team"), ("org_add_team", "Org level can add team"),
            ("user_change_team", "User level can change team"),("team_change_team", "Team level can change team"), ("org_change_team", "Org level can change team"),
            ("user_delete_team", "User level can delete team"),("team_delete_team", "Team level can delete team"), ("org_delete_team", "Org level can delete team"),
        )

