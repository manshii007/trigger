#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
import datetime
import urllib

from rest_framework import (
    viewsets,
    mixins,
    status,
    filters,
    reverse
)

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from rest_framework_extensions.key_constructor.bits import (
    KeyBitBase,
    ListSqlQueryKeyBit,
    RetrieveSqlQueryKeyBit,
    PaginationKeyBit,
    UserKeyBit
)
from rest_framework_extensions.cache.decorators import cache_response
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.encoding import force_text
from django.contrib.contenttypes.models import ContentType

import django_filters

from guardian.shortcuts import (
    assign_perm,
    remove_perm,
    get_objects_for_user,
    get_objects_for_group
)
from guardian.decorators import permission_required_or_403

from permissions.serializers import (
    PermissionSerializer,
    CheckPermissionSerializer
)

from users.serializers import (
    UserSerializer,
    CheckUserSerializer
)
from utils.serializers import CheckFieldsSerializer
from video.serializers import VideoSerializer, CreateVideoSerializer, DetailVideoSerializer
from .models import WorkGroup, Organization, Role, WorkGroupMembership, Team


from permissions.permissions import (
    UserAccessModelPermission,
    CustomObjectPermission,
    CustomDjangoModelPermission,
    get_workgroup_perms_for_model_cls
)
from jobs.models import (
    TaggingJob,
    JobType
)
from jobs.serializers import (
    TaggingJobSerializer,
    WorkgroupTaggingJobSerializer,
    TaggingJobAssignmentSerializer
)
from video.models import Video

from .serializers import (
    GroupSerializer,
    CreateGroupSerializer,
    RetrieveGroupSerializer,
    UpdateGroupSerializer,
    WorkGroupSerializer,
    CreateWorkGroupSerializer,
    RetrieveWorkGroupSerializer,
    UpdateWorkGroupSerializer,
    TeamSerializer,
    CreateTeamSerializer,
    OrganizationSerializer,
    CreateOrganizationSerializer,
    RoleSerializer,
    DetailRoleSerializer,
    WorkGroupMembershipSerializer,
    DetailWorkGroupMembershipSerializer,
    DetailWorkGroupSerializer
)
from .filters import WorkGroupFilter, GroupFilter
User = get_user_model()


# cache testing
class WorkgroupUpdatedAtKeyBit(KeyBitBase):

    def get_data(self, **kwargs):
        key = 'workgroup_api_updated_at_timestamp'
        value = cache.get(key, None)
        if not value:
            value = datetime.datetime.utcnow()
            cache.set(key, value=value)
        return force_text(value)


class CustomObjectKeyConstructor(DefaultKeyConstructor):
    retrieve_sql = RetrieveSqlQueryKeyBit()
    updated_at = WorkgroupUpdatedAtKeyBit()
    user = UserKeyBit()


class CustomListKeyConstructor(DefaultKeyConstructor):
    list_sql = ListSqlQueryKeyBit()
    pagination = PaginationKeyBit()
    updated_at = WorkgroupUpdatedAtKeyBit()
    user = UserKeyBit()


class GroupViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    Creates, Updates, and retrives User Groups
    """
    # TODO change the queryset based on membership
    queryset = Group.objects.all().prefetch_related(
        'user_set').prefetch_related('permissions__content_type')
    serializer_class = GroupSerializer
    permission_classes = (IsAdminUser,)
    action_serializer_classes = {
        "create": CreateGroupSerializer,
        "retrieve": RetrieveGroupSerializer,
        "update": UpdateGroupSerializer
    }
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter)
    filter_class = GroupFilter
    search_fields = ('name',)

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(GroupViewSet, self).get_serializer_class()


class WorkGroupViewSet(
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.UpdateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.DestroyModelMixin,
        viewsets.GenericViewSet):
    queryset = WorkGroup.objects.all().prefetch_related('group__user_set').\
        prefetch_related('group__permissions__content_type')
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated
    )
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter)
    filter_class = WorkGroupFilter
    search_fields = ('name',)
    serializer_class = DetailWorkGroupSerializer
    action_serializer_classes = {
        "create": CreateWorkGroupSerializer,
        "retrieve": RetrieveWorkGroupSerializer,
        "update": UpdateWorkGroupSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(WorkGroupViewSet, self).get_serializer_class()

    def get_queryset(self):
        """
        Allow only group for which you have permissions
        :return: <Queryset object of Workgroup>
        """
        user = self.request.user
        return get_objects_for_user(user, 'workgroups.view_workgroup', with_superuser=True)

    # @cache_response(key_func=CustomObjectKeyConstructor())
    def retrieve(self, *args, **kwargs):
        retrieve_workgroup_data = super(
            WorkGroupViewSet, self).retrieve(*args, **kwargs)
        retrieve_workgroup_data.data['upload_video'] = reverse.reverse('workgroup-upload-video', kwargs=kwargs,
                                                                       request=self.request)
        retrieve_workgroup_data.data['add_member'] = reverse.reverse('workgroup-add-member', kwargs=kwargs,
                                                                     request=self.request)
        retrieve_workgroup_data.data['remove_member'] = reverse.reverse('workgroup-remove-member', kwargs=kwargs,
                                                                        request=self.request)
        retrieve_workgroup_data.data['add_permission'] = reverse.reverse('workgroup-remove-permission', kwargs=kwargs,
                                                                         request=self.request)
        retrieve_workgroup_data.data['remove_permission'] = reverse.reverse('workgroup-remove-permission', kwargs=kwargs,
                                                                            request=self.request)
        retrieve_workgroup_data.data['assign_job'] = reverse.reverse('workgroup-assign-job', kwargs=kwargs,
                                                                     request=self.request)
        retrieve_workgroup_data.data['video_perms'] = reverse.reverse('workgroup-video-perms', kwargs=kwargs,
                                                                      request=self.request)
        # retrieve_workgroup_data.data['videos'] = reverse.reverse('workgroups-videos-list',
        #                                                          kwargs={"workgroups_pk":kwargs['pk']},
        #                                                          request=self.request)
        # retrieve_workgroup_data.data['permissions'] = reverse.reverse('workgroups-permissions-list',
        #                                                          kwargs={"workgroups_pk": kwargs['pk']},
        #                                                          request=self.request)
        # retrieve_workgroup_data.data['tagging_jobs'] = reverse.reverse('workgroups-tagging-jobs',
        #                                                          kwargs=kwargs,
        #                                                          request=self.request)
        retrieve_workgroup_data.data['members'] = reverse.reverse('workgroups-members',
                                                                  kwargs=kwargs,
                                                                  request=self.request)
        retrieve_workgroup_data.data['videos'] = reverse.reverse('workgroups-videos',
                                                                 kwargs=kwargs,
                                                                 request=self.request)
        return retrieve_workgroup_data

    @cache_response(key_func=CustomListKeyConstructor())
    def list(self, *args, **kwargs):
        return super(WorkGroupViewSet, self).list(*args, **kwargs)

    # @cache_response(key_func=CustomListKeyConstructor())
    @detail_route(methods=['get'])
    def members(self, request, pk=None):
        current_workgroup = self.get_object()
        users = current_workgroup.group.user_set
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def videos(self, request, pk=None):
        current_workgroup = self.get_object()
        v = get_objects_for_group(
            current_workgroup.group, 'video.view_video', accept_global_perms=False)
        serializer = VideoSerializer(
            v, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def add_member(self, request, pk=None):
        current_workgroup = self.get_object()
        serializer = CheckUserSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            if 'id' in serializer.validated_data.keys():
                user = get_object_or_404(
                    User, id=serializer.validated_data['id'])
            elif 'username' in serializer.validated_data.keys():
                user = get_object_or_404(
                    User, username=serializer.validated_data['username'])
            else:
                user = get_object_or_404(
                    User, email=serializer.validated_data['email'])
            user.groups.add(current_workgroup.group)
            user.save()
            member_perms_of_workgroup = get_workgroup_perms_for_model_cls(
                current_workgroup, User)
            for perms in member_perms_of_workgroup:
                assign_perm(perms, current_workgroup.group, user)
            message = "User is added to the {} workgroup".format(
                current_workgroup.name)
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def remove_member(self, request, pk=None):
        current_workgroup = self.get_object()
        serializer = CheckUserSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            if 'id' in serializer.validated_data.keys():
                user = get_object_or_404(
                    User, id=serializer.validated_data['id'])
            elif 'username' in serializer.validated_data.keys():
                user = get_object_or_404(
                    User, username=serializer.validated_data['username'])
            else:
                user = get_object_or_404(
                    User, email=serializer.validated_data['email'])
            user.groups.remove(current_workgroup.group)
            user.save()
            message = "User is removed from the {} workgroup".format(
                current_workgroup.name)
            return Response({"message": message, "validated data": serializer.validated_data},
                            status=status.HTTP_200_OK)
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def add_permission(self, request, pk=None):
        current_workgroup = self.get_object()
        serializer = CheckPermissionSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            if 'codename' in serializer.validated_data.keys():
                permission = get_object_or_404(
                    Permission, codename=serializer.validated_data['codename'])
            else:
                permission = get_object_or_404(
                    Permission, name=serializer.validated_data['name'])
            current_workgroup.group.permissions.add(permission)
            current_workgroup.group.save()
            if permission.content_type == ContentType.objects.get_for_model(Video):
                for video in current_workgroup.videolibrary.videos.all():
                    assign_perm(permission, current_workgroup.group, video)
            message = "Permission is added to the {} workgroup".format(
                current_workgroup.name)
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def add_object_perm(self, request, pk=None):
        current_workgroup = self.get_object()
        group = current_workgroup.group
        tmp = urllib.parse.parse_qs(request.body.decode('utf-8'))
        perm = tmp['perm'][0]
        vid = tmp['vid'][0]
        v = Video.objects.filter(id=vid).first()
        if v:
            assign_perm(perm, group, v)
            message = "Permission {} is added to the {} workgroup".format(
                perm, current_workgroup.name)
            return Response(data={"message": message}, status=status.HTTP_201_CREATED)
        return Response(data={"message": "Error in data"}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def remove_permission(self, request, pk=None):
        current_workgroup = self.get_object()
        serializer = CheckPermissionSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            if 'codename' in serializer.validated_data.keys():
                permission = get_object_or_404(
                    Permission, codename=serializer.validated_data['codename'])
            else:
                permission = get_object_or_404(
                    Permission, name=serializer.validated_data['name'])
            current_workgroup.group.permissions.remove(permission)
            current_workgroup.group.save()
            for video in current_workgroup.videolibrary.videos.all():
                remove_perm(permission, current_workgroup.group, video)
            message = "Permission is removed from the {} workgroup".format(
                current_workgroup.name)
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def upload_video(self, request, pk=None):
        current_workgroup = self.get_object()
        video_serializer = CreateVideoSerializer(
            data=request.data, context={"request": request})
        if video_serializer.is_valid():
            uploaded_video = video_serializer.save()
            current_workgroup.videolibrary.videos.add(uploaded_video)
            current_workgroup.videolibrary.save()
            video_perms_of_workgroup = get_workgroup_perms_for_model_cls(
                current_workgroup, Video)
            for perms in video_perms_of_workgroup:
                assign_perm(perms, current_workgroup.group, uploaded_video)
            return Response({"message": " video uploaded"}, status=status.HTTP_201_CREATED)
        else:
            return Response(video_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def add_video(self, request, pk=None):
        current_workgroup = self.get_object()
        video_serializer = CheckFieldsSerializer(
            data=request.data, context={"request": request}, partial=True)
        if video_serializer.is_valid():
            if 'id' in video_serializer.validated_data.keys():
                video = get_object_or_404(
                    Video, id=video_serializer.validated_data['id'])
            else:
                return Response({"message": "invalid reference field for video"}, status=status.HTTP_400_BAD_REQUEST)
            # do we need video library as a separate entity
            current_workgroup.videolibrary.videos.add(video)
            current_workgroup.videolibrary.save()
            video_perms_of_workgroup = get_workgroup_perms_for_model_cls(
                current_workgroup, Video)
            for perms in video_perms_of_workgroup:
                assign_perm(perms, current_workgroup.group, video)
            message = "Video is added to the {} workgroup".format(
                current_workgroup.name)
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"errors": video_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def remove_video(self, request, pk=None):
        current_workgroup = self.get_object()
        video_serializer = CheckFieldsSerializer(
            data=request.data, context={"request": request}, partial=True)
        if video_serializer.is_valid():
            if 'id' in video_serializer.validated_data.keys():
                video = get_object_or_404(
                    Video, id=video_serializer.validated_data['id'])
            else:
                return Response({"message": "invalid reference field for video"}, status=status.HTTP_400_BAD_REQUEST)

            current_workgroup.videolibrary.videos.remove(video)
            current_workgroup.videolibrary.save()
            video_perms_of_workgroup = get_workgroup_perms_for_model_cls(
                current_workgroup, Video)
            for perms in video_perms_of_workgroup:
                remove_perm(perms, current_workgroup.group, video)
            message = "Video is removed from the {} workgroup".format(
                current_workgroup.name)
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"errors": video_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['get'])
    def video_perms(self, request, pk=None):
        workgroup = self.get_object()
        perms = get_workgroup_perms_for_model_cls(workgroup, Video)
        serializer = PermissionSerializer(perms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def assign_job(self, request, pk=None):
        workgroup = self.get_object()
        job_serializer = TaggingJobAssignmentSerializer(data=request.data)
        if job_serializer.is_valid():
            assigned_to_pk = job_serializer.validated_data['workgroup_id']
            job_type_id = job_serializer.validated_data['job_type_id']
            video_id = job_serializer.validated_data['video_id']
            tagging_job = TaggingJob(created_in=workgroup,
                                     assigned_to=get_object_or_404(
                                         WorkGroup, pk=assigned_to_pk),
                                     video=get_object_or_404(
                                         Video, pk=video_id),
                                     created_by=request.user,
                                     job_type=get_object_or_404(
                                         JobType, pk=job_type_id)
                                     )
            tagging_job.save()
            return Response({"data": " created"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"errors": job_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class WorkGroupVideosViewSet(mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet,):
    serializer_class = VideoSerializer
    action_serializer_classes = {
        "create": CreateVideoSerializer,
        "retrieve": DetailVideoSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(WorkGroupVideosViewSet, self).get_serializer_class()

    def get_queryset(self):
        user = self.request.user
        return get_objects_for_user(user, 'video.view_video', with_superuser=True)

    filter_backends = (filters.SearchFilter,)
    search_fields = ('title', 'frametag__tag__name',
                     'frametag__tag__category__name')

    def list(self, request, workgroups_pk=None):
        """List the videos of the workgroup"""
        if request.user.has_perm('workgroups.view_workgroup', get_object_or_404(WorkGroup, pk=workgroups_pk)):
            videos = self.get_queryset().filter(videolibrary__workgroup__pk=workgroups_pk)
            filtered_videos = self.paginate_queryset(
                self.filter_queryset(queryset=videos))
            video_serializer = VideoSerializer(
                filtered_videos, many=True, context={"request": request})
            return Response(video_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "You dont have the object permissions"}, status=status.HTTP_403_FORBIDDEN)

    # def create(self, request,workgroups_pk=None):
    #     if request.user.has_perm('workgroups.view_workgroup', get_object_or_404(WorkGroup, pk=workgroups_pk)):
    #         current_workgroup = get_object_or_404(WorkGroup,pk=workgroups_pk)
    #         video_serializer = CheckFieldsSerializer(data=request.data, context={"request": request}, partial=True)
    #         if video_serializer.is_valid():
    #             if 'id' in video_serializer.validated_data.keys():
    #                video = get_object_or_404(Video, id=video_serializer.validated_data['id'])
    #             else:
    #                 return Response({"message": "invalid reference field for video"}, status=status.HTTP_400_BAD_REQUEST)
    #
    #             current_workgroup.videolibrary.videos.add(video)
    #             current_workgroup.videolibrary.save()
    #             video_perms_of_workgroup = get_workgroup_perms_for_model_cls(current_workgroup, Video)
    #             for perms in video_perms_of_workgroup:
    #                 assign_perm(perms, current_workgroup.group, video)
    #             message = "Video is added to the {} workgroup".format(current_workgroup.name)
    #             return Response({"message": message}, status=status.HTTP_200_OK)
    #         else:
    #             return Response({"errors": video_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    #     else:
    # return Response({"message": "You dont have the object permissions"},
    # status=status.HTTP_403_FORBIDDEN)


class WorkGroupMembersViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        return get_objects_for_user(user, 'users.view_user', with_superuser=True)

    filter_backends = (filters.SearchFilter,)
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def list(self, request, workgroups_pk=None):
        """List the members of the workgroup"""
        if request.user.has_perm('workgroups.view_workgroup', get_object_or_404(WorkGroup, pk=workgroups_pk)):
            members = self.get_queryset().filter(groups__workgroup__pk=workgroups_pk)
            filtered_members = self.paginate_queryset(
                self.filter_queryset(queryset=members))
            member_serializer = UserSerializer(
                filtered_members, many=True, context={"request": request})
            return Response(member_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "You dont have the object permissions"}, status=status.HTTP_403_FORBIDDEN)


class WorkGroupPermissionsViewSet(viewsets.GenericViewSet):
    serializer_class = PermissionSerializer

    queryset = Permission.objects.all()

    filter_backends = (filters.SearchFilter,)
    search_fields = ('codename', 'name')

    def list(self, request, workgroups_pk=None):
        """List the permissions of the workgroup"""
        workgroup = get_object_or_404(WorkGroup, pk=workgroups_pk)
        if request.user.has_perm('workgroups.view_workgroup', workgroup):
            permissions = workgroup.group.permissions.all()
            filtered_permissions = self.paginate_queryset(
                self.filter_queryset(queryset=permissions))
            permission_serializer = PermissionSerializer(
                filtered_permissions, many=True, context={"request": request})
            return Response(permission_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "You dont have the object permissions"}, status=status.HTTP_403_FORBIDDEN)


class WorkGroupTaggingJobsViewSet(viewsets.GenericViewSet):
    serializer_class = WorkgroupTaggingJobSerializer

    queryset = TaggingJob.objects.all()

    filter_backends = (filters.SearchFilter,)
    search_fields = ('video__title', 'video__frametag__tag__name',
                     'video__frametag__tag__category__name')

    def list(self, request, workgroups_pk=None):
        """List the jobs of the workgroup"""
        if request.user.has_perm('workgroups.view_workgroup', get_object_or_404(WorkGroup, pk=workgroups_pk)):
            jobs = self.get_queryset().filter(created_in__pk=workgroups_pk)
            filtered_jobs = self.paginate_queryset(
                self.filter_queryset(queryset=jobs))
            member_serializer = WorkgroupTaggingJobSerializer(
                filtered_jobs, many=True, context={"request": request})
            return Response(member_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"message": "You dont have the object permissions"}, status=status.HTTP_403_FORBIDDEN)


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated, UserAccessModelPermission)
    action_serializer_classes = {
        "create": CreateOrganizationSerializer,
        "update": CreateOrganizationSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(OrganizationViewSet, self).get_serializer_class()

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = (IsAuthenticated, UserAccessModelPermission)
    action_serializer_classes = {
        "create": CreateTeamSerializer,
        "update": CreateTeamSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(OrganizationViewSet, self).get_serializer_class()

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = DetailRoleSerializer
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated
    )
    filter_backends = (filters.SearchFilter,
                       django_filters.rest_framework.DjangoFilterBackend)
    search_fields = ('title',)
    action_serializer_classes = {
        "create": RoleSerializer,
        "update": RoleSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(RoleViewSet, self).get_serializer_class()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        complete_ser = RoleSerializer(
            Role.objects.get(id=serializer.data['id']))
        return Response(complete_ser.data)


class WorkGroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = WorkGroupMembership.objects.all()
    serializer_class = DetailWorkGroupMembershipSerializer
    permission_classes = (
        CustomDjangoModelPermission,
        IsAuthenticated
    )
    action_serializer_classes = {
        "create": WorkGroupMembershipSerializer,
        "update": WorkGroupMembershipSerializer
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(WorkGroupMembershipViewSet, self).get_serializer_class()

    # To accomodate multiple object creation with a single request
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
