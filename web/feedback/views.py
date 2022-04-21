from django.shortcuts import render
from .models import Feedback
from .serializers import FeedbackSerializer
from rest_framework import viewsets, mixins, reverse
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# Create your views here.
class FeedbackViewSet(viewsets.ModelViewSet):
	"""
	Creating Viewset for Feedback
	"""
	serializer_class = FeedbackSerializer
	queryset = Feedback.objects.all()
	permission_classes = (IsAuthenticated,)