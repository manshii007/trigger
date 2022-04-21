#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.contrib.auth.models import Permission

from rest_framework import serializers

from guardian.models import UserObjectPermission

from content.serializers import (
    ContentTypeSerializer,
)


class PermissionSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer(many=False, read_only=True)
    
    class Meta:
        model = Permission
        fields = ('id', 'name', 'content_type')


class UserObjectPermissionSerializer(serializers.ModelSerializer):
    username = serializers.StringRelatedField(source='user')
    content_name = serializers.StringRelatedField(source='content_type')
    permission_name = serializers.StringRelatedField(source='permission')

    class Meta:
        model = UserObjectPermission
        fields = ('id', 'username', 'content_name', 'permission_name', 'object_pk')


class CheckPermissionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    codename = serializers.CharField(max_length=100)
