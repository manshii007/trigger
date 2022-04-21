from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import RO
from guardian.shortcuts import assign_perm


class ROSerializer(ModelSerializer):

    def create(self, validated_data):
        ro = RO.objects.create(**validated_data)
        user = self.context['request'].user
        assign_perm('view_ro', user, ro)
        return ro

    class Meta:
        model = RO
        fields = "__all__"
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}


class DetailROSerializer(ModelSerializer):
    created_by = serializers.SlugRelatedField(read_only=True, slug_field='first_name')

    class Meta:
        model = RO
        fields = ("id", "original_file", "final_file", "channel", "object", "dest", "created_on", "modified_on",
                  "created_by", "title", "process_status", "process_eta", "advertiser", "brand")
