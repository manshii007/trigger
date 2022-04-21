#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from rest_framework.test import APITestCase
from workgroups.models import WorkGroup
from video.models import VideoLibrary
from users.models import User
from guardian.shortcuts import assign_perm, remove_perm
import uuid

class GroupPermissionTestCase(APITestCase):

    def createWorkGroup(self, name):
        group = Group.objects.create(name=str(uuid.uuid4()))
        videolibrary = VideoLibrary.objects.create()
        data = {"name": name}
        workgroup = WorkGroup.objects.create(group=group, videolibrary=videolibrary, **data)
        return workgroup

    def setUp(self):
        """
        Setup 2 user accounts and 2 workgroups
        :return:
        None
        """
        user_1 = User.objects.create_user('test', password='test',
                                     email='test@test.test')
        user_2 = User.objects.create_user('test_2', password='test',
                                       email='test2@test.test')
        workgroup = self.createWorkGroup('test_group')
        user_1.groups.add(workgroup.group)
        user_1.save()

        workgroup_2 = self.createWorkGroup('test_group_2')
        user_2.groups.add(workgroup_2.group)
        user_2.save()
        user_1.groups.add(workgroup_2.group)
        user_1.save()

    def tearDown(self):
        User.objects.all().delete()
        WorkGroup.objects.all().delete()
        Group.objects.all().delete()

    def test_higher_common_permission_between_group(self):
        workgroup_1 = get_object_or_404(WorkGroup, name='test_group')
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')
        assign_perm('video.add_video', workgroup_2.group)
        assign_perm('video.view_video', workgroup_2.group)
        assign_perm('video.view_video', workgroup_1.group)

        user_1 = get_object_or_404(User, username='test')
        user_2 = get_object_or_404(User, username='test_2')

        self.assertTrue(user_1.has_perm('video.add_video'))
        self.assertTrue(user_1.has_perm('video.view_video'))
        self.assertTrue(user_2.has_perm('video.view_video'))
        self.assertTrue(user_2.has_perm('video.add_video'))

        remove_perm('video.add_video', workgroup_2.group)
        user_1 = get_object_or_404(User, username='test')
        user_2 = get_object_or_404(User, username='test_2')

        self.assertFalse(user_1.has_perm('video.add_video'))
        self.assertTrue(user_1.has_perm('video.view_video'))
        self.assertTrue(user_2.has_perm('video.view_video'))
        self.assertFalse(user_2.has_perm('video.add_video'))