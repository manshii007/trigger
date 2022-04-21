from rest_framework import serializers
from .models import Comment
from users.models import User
from tags.models import KeywordTag, FrameTag
from tags.serializers import KeywordTagSerializer, FrameTagSerializer
from users.serializers import UserSerializer
from guardian.shortcuts import assign_perm, ObjectPermissionChecker
from workgroups.models import Group

# class UserSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = User
#         fields = ('id', 'first_name', 'last_name',)


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = Comment
        fields = '__all__'
        # extra_kwargs = {'user': {'default': serializers.CurrentUserDefault(), 'read_only': True}}

    def assign_permissions(self, user, comment):
        permission_list = [
            "org_view_comment", "team_view_comment", "user_view_comment",
            "org_change_comment", "team_change_comment", "user_change_comment",
            "org_delete_comment", "team_delete_comment", "user_delete_comment",
        ]
        for permission in permission_list:
            for group in Group.objects.filter(user=user, permissions__codename=permission):
                assign_perm(permission, group, comment)

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        comment = Comment.objects.create(**validated_data)
        self.assign_permissions(user, comment)
        return comment

# class FrameTagSerializer(serializers.ModelSerializer):
#     tagname = serializers.SerializerMethodField()
#     category = serializers.SerializerMethodField()
#     time = serializers.SerializerMethodField()
#     stopTime = serializers.SerializerMethodField()

#     class Meta:
#         model = FrameTag
#         fields = ('id', 'tagname', 'category', 'video', 'frame_in', 'frame_out', 'comment', 'time', 'stopTime', 'words', 'is_approved')

#     def get_time(self, obj):
#         return obj.frame_in/obj.video.frame_rate

#     def get_stopTime(self, obj):
#         return obj.frame_out/obj.video.frame_rate

#     def get_tagname(self, obj):
#         if obj.tag:
#             return obj.tag.title
#         else:
#             return None

#     def get_category(self,obj):
#         if obj.tag:
#             return obj.category
#         else:
#             return None


# class KeywordTagSerializer(serializers.ModelSerializer):
#     time = serializers.SerializerMethodField()
#     stopTime = serializers.SerializerMethodField()

#     class Meta:
#         model = KeywordTag
#         fields = ('id', 'tags', 'video', 'words', 'frame_in', 'frame_out', 'comment', 'time', 'stopTime', 'sentiment_score', 'sentiment_magnitude', 'is_approved')
#         read_only_fields = ('time', 'stopTime')

#     def get_time(self, obj):
#         return obj.frame_in/obj.video.frame_rate

#     def get_stopTime(self, obj):
#         return obj.frame_out/obj.video.frame_rate


class CommentRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        if isinstance(value, KeywordTag):
            serializer = KeywordTagSerializer(value, context=self.context)
        elif isinstance(value, FrameTag):
            serializer = FrameTagSerializer(value, context=self.context)
        else:
            raise Exception('Unexpected type of tagged object')

        return serializer.data


class DetailCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    content_object = CommentRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ("id","user","comment", "content_object", "submit_datetime")
        read_only_fields = ("content_object",)



