from django.shortcuts import render
from. models import Comment
from .serializers import CommentSerializer, DetailCommentSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = DetailCommentSerializer
    queryset = Comment.objects.all()
    permission_classes = (IsAuthenticated,)
    action_serializer_classes = {
        "create": CommentSerializer,
        "update": CommentSerializer,
        "retrieve": DetailCommentSerializer,
    }

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CommentViewSet, self).get_serializer_class()