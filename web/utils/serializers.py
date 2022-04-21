from rest_framework import serializers


class CheckFieldsSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()