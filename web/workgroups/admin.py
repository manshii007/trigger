#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.contrib import admin
from admin import admin_site
from .models import WorkGroup,  Organization, Role, WorkGroupMembership
from guardian.admin import GuardedModelAdmin
# Register your models here.


class WorkGroupAdmin(GuardedModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "organization", "owner")

class OrganizationAdmin(GuardedModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "owner")


class RoleAdmin(GuardedModelAdmin):
    search_fields = ("title",)
    list_display = ("title",)
    filter_horizontal = ("permissions",)


class WorkGroupMembershipAdmin(GuardedModelAdmin):
    search_fields = ("title",)
    list_display = ("user", "workgroup", "created_on", "modified_on")
    filter_horizontal = ("role",)

admin.site.register(WorkGroup, WorkGroupAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(WorkGroupMembership, WorkGroupMembershipAdmin)
