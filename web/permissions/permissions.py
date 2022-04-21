from rest_framework.permissions import DjangoObjectPermissions, DjangoModelPermissions
from django.contrib.contenttypes.models import ContentType
from workgroups.models import WorkGroupMembership, Permission, Role, Team, Group
from content.models import Channel
from functools import reduce
import operator
from django.db.models import Q
from rest_framework.response import Response

class CustomObjectPermission(DjangoObjectPermissions):
    SAFE_METHODS = ()
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.d elete_%(model_name)s'],
    }


def get_workgroup_perms_for_model_cls(workgroup, model_cls):
    content_type_for_model_cls = ContentType.objects.get_for_model(model_cls)
    permissions_related_to_video = workgroup.group.permissions.filter(content_type=content_type_for_model_cls,)
    return permissions_related_to_video


class CustomDjangoModelPermission(DjangoModelPermissions):

    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def _queryset(self, view):
        assert hasattr(view, 'get_queryset') \
               or getattr(view, 'queryset', None) is not None, (
            'Cannot apply {} on a view that does not set '
            '`.queryset` or have a `.get_queryset()` method.'
        ).format(self.__class__.__name__)

        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
            assert queryset is not None, (
                '{}.get_queryset() returned None'.format(view.__class__.__name__)
            )
            return queryset
        return view.queryset

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        # modify has_permission to include change in permission structure here
        # modify how the function uses has_perm
        if getattr(view, '_ignore_model_permissions', False):
            return True

        if not request.user or (
                not request.user.is_authenticated and self.authenticated_users_only):
            return False

        if request.user and request.user.is_superuser:
            return True

        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.model)
        codenames = [perm.split(".")[1] for perm in perms]
        user_all_memberships = WorkGroupMembership.objects.filter(user=request.user)
        user_all_roles = Role.objects.filter(workgroupmembership__in=user_all_memberships)
        user_all_perms = Permission.objects.filter(role__in=user_all_roles)
        if user_all_perms.filter(codename__in=codenames):
            return True
        else:
            return False


class CustomDjangoContentPermission(DjangoModelPermissions):

    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def get_channel_perms(self):
        channels = Channel.objects.all()
        channel_perms = ["can_access_{}".format(channel.channel_name.lower().replace(" ", "_")) for channel in channels]
        return channel_perms

    def _queryset(self, view):
        assert hasattr(view, 'get_queryset') \
               or getattr(view, 'queryset', None) is not None, (
            'Cannot apply {} on a view that does not set '
            '`.queryset` or have a `.get_queryset()` method.'
        ).format(self.__class__.__name__)

        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
            assert queryset is not None, (
                '{}.get_queryset() returned None'.format(view.__class__.__name__)
            )
            return queryset
        return view.queryset

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        # modify has_permission to include change in permission structure here
        # modify how the function uses has_perm
        if getattr(view, '_ignore_model_permissions', False):
            return True

        if not request.user or (
                not request.user.is_authenticated and self.authenticated_users_only):
            return False

        if request.user and request.user.is_superuser:
            return True

        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.model)
        codenames = [perm.split(".")[1] for perm in perms]
        user_all_memberships = WorkGroupMembership.objects.filter(user=request.user)
        user_all_roles = Role.objects.filter(workgroupmembership__in=user_all_memberships)
        user_all_perms = Permission.objects.filter(role__in=user_all_roles)
        if user_all_perms.filter(codename__in=codenames):
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        # authentication checks have already executed via has_permission
        if request.user and request.user.is_superuser:
            return True

        user_all_memberships = WorkGroupMembership.objects.filter(user=request.user)
        user_all_roles = Role.objects.filter(workgroupmembership__in=user_all_memberships)
        user_all_perms = list(Permission.objects.filter(role__in=user_all_roles).values_list("codename", flat=True))
        channel_perms = self.get_channel_perms()
        allowed_channel_perms = list(filter(lambda x: x in user_all_perms, channel_perms))
        allowed_channels = [x.replace("can_access_","").replace("_"," ") for x in allowed_channel_perms]
        if not obj.channel or obj.channel.channel_name.lower() not in allowed_channels:
            # If the user does not have permissions we need to determine if
            # they have read permissions to see 403, or not, and simply see
            # a 404 response.obj.channel.channel_name
            # Has read permissions.
            return False
        elif obj.channel and obj.channel.channel_name and obj.channel.channel_name.lower() in allowed_channels:
            return True
        else:
            return False


class ContentChannelControlMixin:
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        user_all_memberships = WorkGroupMembership.objects.filter(user=request.user)
        user_all_roles = Role.objects.filter(workgroupmembership__in=user_all_memberships)
        user_all_perms = list(Permission.objects.filter(role__in=user_all_roles).values_list("codename", flat=True))
        channels = Channel.objects.all()
        channel_perms = ["can_access_{}".format(channel.channel_name.lower().replace(" ", "_")) for channel in channels]
        allowed_channel_perms = list(filter(lambda x: x in user_all_perms, channel_perms))
        allowed_channels = [x.replace("can_access_", "").replace("_", " ") for x in allowed_channel_perms]
        if allowed_channels:
            query = reduce(operator.or_, (Q(channel__channel_name__iexact=x) for x in allowed_channels))
            queryset = queryset.filter(query)
        else:
            queryset = queryset.filter(pk__isnull=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class UserAccessModelPermission(DjangoModelPermissions):

    perms_map = {
        'GET': ['org_view_%(model_name)s','team_view_%(model_name)s', 'user_view_%(model_name)s'],
        'OPTIONS': ['org_view_%(model_name)s','team_view_%(model_name)s', 'user_view_%(model_name)s'],
        'HEAD': ['org_view_%(model_name)s','team_view_%(model_name)s', 'user_view_%(model_name)s'],
        'POST': ['org_add_%(model_name)s','team_add_%(model_name)s', 'user_add_%(model_name)s'],
        'PUT': ['org_change_%(model_name)s','team_change_%(model_name)s', 'user_change_%(model_name)s'],
        'PATCH': ['org_change_%(model_name)s','team_change_%(model_name)s', 'user_change_%(model_name)s'],
        'DELETE': ['org_delete_%(model_name)s','team_delete_%(model_name)s', 'user_delete_%(model_name)s'],
    }

    authenticated_users_only = True
    def get_required_permissions(self, method, model_cls):
        print(method)
        """
        Given a model and an HTTP method, return the list of permission
        codes that the user is required to have.
        """
        kwargs = {
            'model_name': model_cls._meta.model_name
        }

        if method not in self.perms_map:
            raise exceptions.MethodNotAllowed(method)

        return [perm % kwargs for perm in self.perms_map[method]]

    def _queryset(self, view):
        assert hasattr(view, 'get_queryset') or getattr(view, 'queryset', None) is not None, (
            'Cannot apply {} on a view that does not set '
            '`.queryset` or have a `.get_queryset()` method.'
        ).format(self.__class__.__name__)

        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
            assert queryset is not None, (
                '{}.get_queryset() returned None'.format(view.__class__.__name__)
            )
            return queryset
        return view.queryset

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, '_ignore_model_permissions', False):
            return True

        if not request.user or (
                not request.user.is_authenticated and self.authenticated_users_only):
            return False

        queryset = self._queryset(view)
        req_perms = self.get_required_permissions(request.method, queryset.model)
        all_perms = list(Group.objects.filter(user=request.user).values_list("permissions__codename", flat=True))
        return any(x in req_perms for x in all_perms)

