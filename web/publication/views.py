from django.shortcuts import render
from .models import Publication
from .serializers import PublicationSerializer
from rest_framework import viewsets, mixins, reverse
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# Create your views here.
class PublicationViewSet(viewsets.ModelViewSet):
	"""
	Creating Viewset for Publication
	"""
	serializer_class = PublicationSerializer
	queryset = Publication.objects.all()
	permission_classes = (IsAuthenticated,)