#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from rest_framework import (
    viewsets,
    mixins,
    views,
    status
)
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.filters import DjangoObjectPermissionsFilter
from rest_framework.decorators import list_route, api_view, parser_classes, authentication_classes, permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from guardian.shortcuts import get_objects_for_user
from io import BytesIO
import django_filters
from workgroups.serializers import (
    GroupPermissionsSerializer
)
from workgroups.models import (
    WorkGroup
)

from .permissions import (
    IsAdminOrIsUserOrNothing,
    IsUserOrReadOnly,
    YourProfileOrNothing
)
from .serializers import (
    ProfilePasswordSerializer,
    ChangePasswordSerializer,
    CreateUserSerializer,
    UserSerializer,
    DetailUserSerializer,
    ProfileSerializer,
    DetailProfileSerializer,
    DetailJobUserSerializer,
    NotificationSerializer
)
from .models import (
    Profile,
    User
)
from jobs.models import ReviewTranslationJob, MovieTranslationJob, EpisodeTranslationJob

from utils.printing import MyPrint

from pagination.pagination import StandardResultsSetPagination

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .filters import (
    UserWorkGroupFilter,
)


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    Creates, Updates, and retrieves User accounts
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # filter_backends = (DjangoObjectPermissionsFilter,)
    action_serializer_classes = {
        "create": CreateUserSerializer,
        "retrieve": DetailUserSerializer
    }
    permission_classes = (IsAdminOrIsUserOrNothing, )
    filter_backends = ( filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    search_fields = ('first_name', 'last_name')
    ordering_fields = ('first_name', 'last_name')

    def get_queryset(self):
        return User.objects.all().filter(id=self.request.user.id)

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(UserViewSet, self).get_serializer_class()

    @list_route(methods=['get'])
    def print_users(self, request):
        # Create the HttpResponse object with the appropriate PDF headers.
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="My Users.pdf"'

        buffer = BytesIO()

        report = MyPrint(buffer, 'Letter')
        pdf = report.print_users()

        response.write(pdf)
        return response


class AllUserViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """
    Creates, Updates, and retrieves User accounts
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    action_serializer_classes = {
        "create": CreateUserSerializer,
        "retrieve": DetailUserSerializer
    }
    permission_classes = (IsAdminOrIsUserOrNothing, )
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = UserWorkGroupFilter
    search_fields = ('first_name', 'last_name')
    ordering_fields = ('first_name', 'last_name')

    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(AllUserViewSet, self).get_serializer_class()

    @list_route(methods=['get'])
    def print_users(self, request):
        # Create the HttpResponse object with the appropriate PDF headers.
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="My Users.pdf"'

        buffer = BytesIO()

        report = MyPrint(buffer, 'Letter')
        pdf = report.print_users()

        response.write(pdf)
        return response


class UserPermissionsViewSet(viewsets.ViewSet):
    """Display user permissions and the workgroup they were obtained through"""
    def list(self, request, users_pk=None):
        """List all the permissions given to the user"""
        workgroups = WorkGroup.objects.all().filter(group__user__pk=users_pk)
        print(workgroups)
        serializer = GroupPermissionsSerializer(workgroups, context={'request':request}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationsViewSet(viewsets.ViewSet):
    """Display user permissions and the workgroup they were obtained through"""
    
    @list_route(methods=['get'])
    def mark_read(self, request):
        notification_ids = request.query_params.get("ids", None)
        user = request.user

        if notification_ids:
            notification_ids = notification_ids.split(",")
            notifications = []
            for i in notification_ids:
                notification_obj = Notification.objects.filter(pk = i).first()
                notifications.append(notification_obj)
                notification_obj.mark_as_read()
                notification_obj.save()
        elif user:
            notifications = Notification.objects.filter(recipient=user, unread=True, deleted=False).mark_all_as_read()
        notifications = Notification.objects.filter(recipient=user, deleted=False).order_by('-timestamp')[:40]
        unread_count = user.notifications.unread().count()

        serializer = NotificationSerializer(notifications, context={'request':request}, many=True)
        return Response({'results': serializer.data, 'unread': unread_count}, status=status.HTTP_200_OK)

    def list(self, request, users_pk=None):
        """List all the permissions given to the user"""
        usr = request.user
        notifications = Notification.objects.filter(recipient=usr, deleted=False).order_by('-timestamp')[:40]
        unread_count = usr.notifications.unread().count()

        serializer = NotificationSerializer(notifications, context={'request':request}, many=True)
        return Response({'results': serializer.data, 'unread': unread_count}, status=status.HTTP_200_OK)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    permission_classes = (YourProfileOrNothing,)
    serializer_class = ProfileSerializer
    action_serializer_classes = {
        "retrieve": DetailProfileSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(ProfileViewSet, self).get_serializer_class()


class HealthCheck(views.APIView):
    """
    Return 404 for health check for google cloud
    """
    permission_classes = (IsUserOrReadOnly,)

    def get(self, request, format=None):
        """
        :param request:
        :param format:
        :return:
         404 response
        """
        return Response({'message': ''}, status=status.HTTP_404_NOT_FOUND)


class JobUserViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """
    Creates, Updates, and retrieves User accounts
    """
    queryset = User.objects.all()
    serializer_class = DetailJobUserSerializer
    pagination_class = StandardResultsSetPagination
    # filter_backends = (DjangoObjectPermissionsFilter,)
    action_serializer_classes = {
        "create": CreateUserSerializer,
        "retrieve": DetailJobUserSerializer
    }
    permission_classes = (IsAdminOrIsUserOrNothing, )
    filter_backends = ( filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter)
    search_fields = ('first_name', 'last_name')
    ordering_fields = ('first_name', 'last_name')

    def get_queryset(self):
        qs = User.objects.all()
        qs = qs.prefetch_related("movie_translation_job_assigned", "episode_translation_job_assigned",
                                 "movie_translation_job_assigned__movie",
                                 "movie_translation_job_assigned__movie_segment",
                                 "episode_translation_job_assigned__episode_segment",
                                 "episode_translation_job_assigned__episode",
                                 )
        return qs

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(JobUserViewSet, self).get_serializer_class()

class ProfilePasswordViewSet(APIView):
    """
    An endpoint for updating password from profile page.
    """
    permission_classes = []
    authentication_classes = [IsAuthenticated]

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request, *args, **kwargs):
        serializer = ProfilePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            old_password = serializer.data.get("old_password").strip()
            new_password = serializer.data.get("new_password").strip()
            id = serializer.data.get("id")
            user = User.objects.get(pk=id)
            if user:
                if not user.check_password(old_password):
                    return Response({"message": "wrong password"},
                                    status=status.HTTP_400_BAD_REQUEST)
                # set_password also hashes the password that the user will get
                user.set_password(new_password)
                user.save()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response({"msg":"User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdatePasswordViewSet(APIView):
    """
    An endpoint for changing password.
    """
    permission_classes = []
    authentication_classes = []

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            old_password = serializer.data.get("token")
            user = User.objects.filter(forgot_password_token=old_password)
            try:
                user = user[0]
                if not old_password == user.forgot_password_token:
                    return Response({"token": ["invalid token"]},
                                    status=status.HTTP_400_BAD_REQUEST)
                # set_password also hashes the password that the user will get
                user.set_password(serializer.data.get("new_password"))
                user.forgot_password_token = None
                user.save()
                return Response(status=status.HTTP_200_OK)
            except:
                return Response({"msg":"User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
# @parser_classes((JSONParser,))
@authentication_classes([])
@permission_classes([])
def forgot_password(request):
    email = request.data.get("email", None)
    try:
        user = User.objects.get(email=email)
        message = Mail(from_email='Tessact Support <no-reply@tessact.com>', to_emails=[email])
        forgot_password_token = default_token_generator.make_token(user)
        user.forgot_password_token = forgot_password_token
        user.save()
        message.dynamic_template_data = {
            "auth_token": forgot_password_token,
            "username": user.first_name
        }
        # to-do: replace this with template for forgot password
        message.template_id = "d-512236020a1347ccbeee5c00ce12664f"
        try:
            sg = SendGridAPIClient("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")
            response = sg.send(message)
            return Response({"data": "Please check your inbox to reset your password"}, status=status.HTTP_200_OK)
        except Exception as e:
            print("Error: {0}".format(e))
            print(e.body)
            return Response({"data": "error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except User.DoesNotExist:
        return Response({"data": "user does not exist"}, status=status.HTTP_404_NOT_FOUND)
