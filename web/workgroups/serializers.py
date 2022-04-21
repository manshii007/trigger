#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from rest_framework import (
    serializers
)
from django.contrib.auth.models import (
    Group,
    Permission
)
from guardian.shortcuts import assign_perm, remove_perm

import uuid

from users.models import User

from video.models import (
    VideoLibrary
)
from video.serializers import (
    VideoLibrarySerializer,
    VideoSerializer
)

from .models import WorkGroup, Organization, Role, WorkGroupMembership, Team

from permissions.serializers import (
    PermissionSerializer
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')

class GroupSerializer(serializers.ModelSerializer):
    user_set = UserSerializer(many=True)
    permissions = PermissionSerializer(many=True)

    class Meta:
        model = Group
        fields = ('url', 'id', 'name', 'user_set', 'permissions')


class CreateGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)
        read_only_fields = ('name',)


class RetrieveGroupSerializer(serializers.ModelSerializer):
    user_set = UserSerializer(many=True, read_only=True)
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'user_set', 'permissions')


class UpdateGroupSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all().exclude(email=""), write_only=True)
    permission = serializers.PrimaryKeyRelatedField(queryset=Permission.objects.all(), write_only=True)
    ACTIONS = (
        ('NAN', 'None'),
        ('ADD_USER', 'Add User'),
        ('RM_USER', 'Remove User'),
        ('ADD_PERM', 'Add Permission'),
        ('RM_PERM', "Remove Permission")
    )
    choice = serializers.ChoiceField(ACTIONS, allow_blank=False, write_only=True)

    class Meta:
        model = Group
        fields = ('user', 'permission', 'choice')

    def update(self, instance, validated_data):
        """Set the export code here"""
        # print(validated_data)
        # instance.name = validated_data.get('name', instance.name)
        # get data from validate_data
        user = validated_data.get('user')
        choice = validated_data.get('choice')
        permission = validated_data.get('permission')
        # update group based on the choice
        if choice == 'ADD_USER':
            # check if the user is part of the group
            if instance.user_set.filter(id=user.id):
                # user is already in the group
                pass
            else:
                # user is not part of the group
                # add user to the group
                user.groups.add(instance)
        elif choice == 'RM_USER':
            # check if the user is part of the group
            if instance.user_set.filter(id=user.id):
                # user is already in the group
                # remove user from the group
                user.groups.remove(instance)
            else:
                # user is not part of the group
                pass
        elif choice == 'RM_PERM':
            # check if the workgroup has the permission
            if instance.permissions.filter(id=permission.id):
                # workgroup have the permission
                instance.permissions.remove(permission)
            else:
                # workgroup doesn't have the permission
                pass
        elif choice == 'ADD_PERM':
            # check if the workgroup has the permission
            if instance.permissions.filter(id=permission.id):
                # workgroup have the permission
                pass
            else:
                # workgroup doesn't have the permission
                instance.permissions.add(permission)
                pass
        else:
            pass
        instance.save()
        return instance


class GroupPermissionsSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(source='group.permissions', read_only=True, many=True)

    class Meta:
        model = WorkGroup
        fields = ('url', 'name', 'permissions')

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class DetailRoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = "__all__"


class WorkGroupMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkGroupMembership
        fields = "__all__"

class WorkGroupSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = WorkGroup
        fields = ('url', 'id', 'name', 'member_count')

    def get_member_count(self, obj):
        g = obj.group
        users = User.objects.filter(groups=g)
        return users.count()

class DetailWorkGroupMembershipSerializer(serializers.ModelSerializer):
    role = DetailRoleSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True, many=False)
    workgroup = WorkGroupSerializer(read_only=True, many=False)

    class Meta:
        model = WorkGroupMembership
        fields = "__all__"

class DetailMembershipSerializer(serializers.ModelSerializer):
    role = DetailRoleSerializer(many=True, read_only=True)
    workgroup = WorkGroupSerializer(read_only=True, many=False)

    class Meta:
        model = WorkGroupMembership
        fields = "__all__"

class DetailWorkGroupSerializer(serializers.ModelSerializer):
    # members = UserSerializer(source='group.user_set', many=True)
    # permissions = PermissionSerializer(source='group.permissions', many=True)
    # videos = VideoSerializer(source='videolibrary.videos', many=True)
    member_count = serializers.SerializerMethodField(read_only=True)
    members = DetailWorkGroupMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = WorkGroup
        fields = ('url', 'id', 'name', 'members', 'member_count')

    def get_member_count(self, obj):
        g = obj.group
        users = User.objects.filter(groups=g)
        return users.count()


class CreateWorkGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkGroup
        fields = ('name',)
        extra_kwargs = {'owner': {'default': serializers.CurrentUserDefault(), "read_only": True}}

    def create(self, validated_data):
        """ transfer group data to group object"""
        # create new group whenever a new workgroup is created
        group_object = Group.objects.create(name=str(uuid.uuid4()))
        videolibrary = VideoLibrary.objects.create()
        workgroup = WorkGroup.objects.create(group=group_object, videolibrary=videolibrary, **validated_data)
        # global perms
        assign_perm('workgroups.view_workgroup', workgroup.group)
        assign_perm('users.view_user', workgroup.group)
        # object perms
        assign_perm('workgroups.view_workgroup', workgroup.group, workgroup)

        # add user to the group
        user = self.context['request'].user
        user.groups.add(group_object)

        return workgroup


class RetrieveWorkGroupSerializer(serializers.ModelSerializer):
    members = UserSerializer(source='group.user_set', many=True)
    permissions = PermissionSerializer(source='group.permissions', many=True)
    videos = VideoSerializer(source='videolibrary.videos', many=True)

    class Meta:
        model = WorkGroup
        fields = ('id', 'name', 'members', 'permissions', 'videos')


class UpdateWorkGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkGroup
        fields = ('name',)

    # def update(self, instance, validated_data):
    #     """ update the group data"""
    #     group_data = validated_data.get('group')
    #     group = instance.group
    #     # get data from validate_data
    #     user = group_data['user']
    #     choice = group_data['choice']
    #     permission = group_data['permission']
    #     # update group based on the choice
    #     if choice == 'ADD_USER':
    #         # check if the user is part of the group
    #         if instance.group.user_set.filter(id=user.id):
    #             # user is already in the group
    #             pass
    #         else:
    #             # user is not part of the group
    #             # add user to the group
    #             user.groups.add(instance.group)
    #     elif choice == 'RM_USER':
    #         # check if the user is part of the group
    #         if instance.group.user_set.filter(id=user.id):
    #             # user is already in the group
    #             # remove user from the group
    #             user.groups.remove(instance.group)
    #         else:
    #             # user is not part of the group
    #             pass
    #     elif choice == 'RM_PERM':
    #         # check if the workgroup has the permission
    #         if instance.group.permissions.filter(id=permission.id):
    #             # workgroup have the permission
    #             instance.group.permissions.remove(permission)
    #         else:
    #             # workgroup doesn't have the permission
    #             pass
    #     elif choice == 'ADD_PERM':
    #         # check if the workgroup has the permission
    #         if instance.group.permissions.filter(id=permission.id):
    #             # workgroup have the permission
    #             pass
    #         else:
    #             # workgroup doesn't have the permission
    #             instance.group.permissions.add(permission)
    #             pass
    #     else:
    #         pass
    #     instance.group.save()
    #
    #     # update the name
    #     instance.name = validated_data.get('name', instance.name)
    #     instance.save()
    #
    #     return instance


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'

class CreateTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('name')
        extra_kwargs = {'owner': {'default': serializers.CurrentUserDefault(), "read_only": True}}

class CreateOrganizationSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True,many=True)
    class Meta:
        model = Team
        fields = ('name','organization', 'group')
        extra_kwargs = {'owner': {'default': serializers.CurrentUserDefault(), "read_only": True}}
