#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#

from rest_framework.test import APITestCase
from rest_framework import (
    status,
    reverse,
)
from rest_framework.authtoken.models import Token

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Permission
from django.conf import settings

from guardian.shortcuts import (
    assign_perm
)
import uuid, os

from users.models import User

from video.models import VideoLibrary, Video

from .models import WorkGroup, Group


class WorkgroupCreationTests(APITestCase):
    test_dir = os.path.join(settings.BASE_DIR, 'tests')
    video_path = os.path.join(test_dir, 'test_video_upload/small_video.mp4')
    post_path = os.path.join(test_dir, 'test_video_upload/A_Day_In_The_Life.jpg')

    def createWorkGroup(self, name):
        group = Group.objects.create(name=str(uuid.uuid4()))
        videolibrary = VideoLibrary.objects.create()
        data = {"name": name}
        workgroup = WorkGroup.objects.create(group=group, videolibrary=videolibrary, **data)
        return workgroup

    def createDummyVideo(self, library):
        # post a video to video-list url
        url = reverse.reverse('video-list')

        data = {
            "title": "test_video",
            "file": open(self.video_path, 'rb'),
            "poster": open(self.post_path, 'rb')
        }
        self.client.post(url, data=data, format='multipart')
        video = get_object_or_404(Video, title='test_video')
        library.videos.add(video)
        return video

    def setUp(self):
        u = User.objects.create_user('test', password='test',
                                     email='test@test.test')
        u_2 = User.objects.create_user('test_2', password='test',
                                     email='test2@test.test')
        # create a workgroup for user
        workgroup = self.createWorkGroup('test_group')
        u.groups.add(workgroup.group)
        u.save()

        # dummy group
        workgroup_2 = self.createWorkGroup('test_group_2')
        u_2.groups.add(workgroup_2.group)
        u_2.save()

        assign_perm('video.add_video', workgroup.group)
        assign_perm('video.view_video', workgroup.group)

        # authorize the APIClient
        auth_token = Token.objects.get(user__username='test')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + auth_token.key)

        # dummy video addition
        video = self.createDummyVideo(workgroup_2.videolibrary)

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key('test')
            u.delete()
            User.objects.all().delete()

        except ObjectDoesNotExist:
            print("error in u delete")
            pass
        WorkGroup.objects.all().delete()
        Group.objects.all().delete()
        Video.objects.all().delete()

    def test_workgroup_create_with_all_permission(self):
        # give 'add_workgroup' permission to 'test_group'
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission,codename='add_workgroup'))

        # request and response
        url = reverse.reverse('workgroup-list')
        data = {
            "name":"test_workgroup_create_with_permission"
        }
        response = self.client.post(url,data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WorkGroup.objects.count(), 3)
        self.assertEqual(Group.objects.get(id=3).workgroup.name, "test_workgroup_create_with_permission")

    def test_workgroup_create_without_permission(self):
        url = reverse.reverse('workgroup-list')
        data = {
            "name": "test_workgroup_create_with_permission"
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(WorkGroup.objects.count(), 2)
        self.assertEqual(Group.objects.get(id=1).workgroup.name, "test_group")


class WorkGroupMemberTests(APITestCase):
    test_dir = os.path.join(settings.BASE_DIR, 'tests')
    video_path = os.path.join(test_dir, 'test_video_upload/small_video.mp4')
    post_path = os.path.join(test_dir, 'test_video_upload/A_Day_In_The_Life.jpg')

    def createWorkGroup(self, name):
        group = Group.objects.create(name=str(uuid.uuid4()))
        videolibrary = VideoLibrary.objects.create()
        data = {"name": name}
        workgroup = WorkGroup.objects.create(group=group, videolibrary=videolibrary, **data)
        return workgroup

    def createDummyVideo(self, library):
        # post a video to video-list url
        url = reverse.reverse('video-list')

        data = {
            "title": "test_video",
            "file": open(self.video_path, 'rb'),
            "poster": open(self.post_path, 'rb')
        }
        self.client.post(url, data=data, format='multipart')
        video = get_object_or_404(Video, title='test_video')
        library.videos.add(video)
        return video

    def setUp(self):
        u = User.objects.create_user('test', password='test',
                                     email='test@test.test')
        u_2 = User.objects.create_user('test_2', password='test',
                                       email='test2@test.test')
        # create a workgroup for user
        workgroup = self.createWorkGroup('test_group')
        u.groups.add(workgroup.group)
        u.save()

        # dummy group
        workgroup_2 = self.createWorkGroup('test_group_2')
        u_2.groups.add(workgroup_2.group)
        u_2.save()

        assign_perm('video.add_video', workgroup.group)
        assign_perm('video.view_video', workgroup.group)

        # authorize the APIClient
        auth_token = Token.objects.get(user__username='test')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + auth_token.key)

        # dummy video addition
        video = self.createDummyVideo(workgroup_2.videolibrary)

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key('test')
            u.delete()
            User.objects.all().delete()

        except ObjectDoesNotExist:
            print("error in u delete")
            pass
        WorkGroup.objects.all().delete()
        Group.objects.all().delete()
        Video.objects.all().delete()

    def test_add_member_to_workgroup_with_all_permission(self):
        # give only 'change_workgroup' permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='add_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # assign perm
        assign_perm('view_workgroup', workgroup.group, workgroup_2)
        assign_perm('add_workgroup', workgroup.group, workgroup_2)

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        add_member_url = url+"add_member/"
        # create a bogus user
        u2 = User.objects.create_user('bogususer', password='test2',
                                      email='bogus@test.test')
        u2.save()
        data = {
            "email": "bogus@test.test"
        }

        response = self.client.post(add_member_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(u2.groups.get().workgroup.name, "test_group_2")

    def test_add_member_to_workgroup_without_add_permission_without_view_permission(self):
        workgroup = get_object_or_404(WorkGroup, name='test_group')

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        add_member_url = url+"add_member/"

        # create a bogus user
        u2 = User.objects.create_user('bogususer', password='test2',
                                      email='bogus@test.test')
        u2.save()
        data = {
            "username": "bogususer"
        }

        response = self.client.post(add_member_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(u2.groups.all().count(), 0)

    def test_add_member_to_workgroup_without_add_permission_with_view_permission(self):
        workgroup = get_object_or_404(WorkGroup, name='test_group')

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        add_member_url = url+"add_member/"

        # create a bogus user
        u2 = User.objects.create_user('bogususer', password='test2',
                                      email='bogus@test.test')
        u2.save()
        data = {
            "username": "bogususer"
        }
        response = self.client.post(add_member_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(u2.groups.all().count(), 0)

    def test_remove_member_from_workgroup_with_all_permission(self):
        # give only 'add_workgroup' permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='add_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # assign perm
        assign_perm('view_workgroup', workgroup.group, workgroup_2)
        assign_perm('add_workgroup', workgroup.group, workgroup_2)

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        remove_member_url = url+"remove_member/"

        # create a bogus user
        u2 = User.objects.create_user('bogususer', password='test2',
                                      email='bogus@test.test')
        u2.save()
        data = {
            "email": "bogus@test.test"
        }

        # add the user to group
        u2.groups.add(workgroup_2.group)

        response = self.client.post(remove_member_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(u2.groups.all().count(), 0)

    def test_remove_member_from_workgroup_without_add_permission_without_view_permission(self):
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        remove_member_url = url+"remove_member/"

        # create a bogus user
        u2 = User.objects.create_user('bogususer', password='test2',
                                      email='bogus@test.test')
        u2.save()
        data = {
            "email": "bogus@test.test"
        }

        # add the user to group
        u2.groups.add(workgroup_2.group)

        response = self.client.post(remove_member_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(u2.groups.all().count(), 1)

    def test_remove_member_from_workgroup_without_add_permission_with_view_permission(self):
        # give only the "view_workgroup" permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='view_workgroup'))
        assign_perm('view_workgroup', workgroup.group, workgroup)

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        remove_member_url = url+"remove_member/"

        # create a bogus user
        u2 = User.objects.create_user('bogususer', password='test2',
                                      email='bogus@test.test')
        u2.save()
        data = {
            "email": "bogus@test.test"
        }
        # add the user to group
        u2.groups.add(workgroup_2.group)

        response = self.client.post(remove_member_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(u2.groups.all().count(), 1)

    def test_list_members_with_all_permission(self):
        # give only the "change_workgroup" permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='view_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # assign perm
        assign_perm('view_workgroup', workgroup.group, workgroup_2)

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        list_members_url = url + "members/"

        response = self.client.get(list_members_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_members_with_model_view_permission_without_object_view_permission(self):
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='view_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        list_members_url = url + "members/"

        response = self.client.get(list_members_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



class WorkGroupPermsTests(APITestCase):
    test_dir = os.path.join(settings.BASE_DIR, 'tests')
    video_path = os.path.join(test_dir, 'test_video_upload/small_video.mp4')
    post_path = os.path.join(test_dir, 'test_video_upload/A_Day_In_The_Life.jpg')

    def createWorkGroup(self, name):
        group = Group.objects.create(name=str(uuid.uuid4()))
        videolibrary = VideoLibrary.objects.create()
        data = {"name": name}
        workgroup = WorkGroup.objects.create(group=group, videolibrary=videolibrary, **data)
        return workgroup

    def createDummyVideo(self, library):
        # post a video to video-list url
        url = reverse.reverse('video-list')

        data = {
            "title": "test_video",
            "file": open(self.video_path, 'rb'),
            "poster": open(self.post_path, 'rb')
        }
        self.client.post(url, data=data, format='multipart')
        video = get_object_or_404(Video, title='test_video')
        library.videos.add(video)
        return video

    def setUp(self):
        u = User.objects.create_user('test', password='test',
                                     email='test@test.test')
        u_2 = User.objects.create_user('test_2', password='test',
                                       email='test2@test.test')
        # create a workgroup for user
        workgroup = self.createWorkGroup('test_group')
        u.groups.add(workgroup.group)
        u.save()

        # dummy group
        workgroup_2 = self.createWorkGroup('test_group_2')
        u_2.groups.add(workgroup_2.group)
        u_2.save()

        assign_perm('video.add_video', workgroup.group)
        assign_perm('video.view_video', workgroup.group)

        # authorize the APIClient
        auth_token = Token.objects.get(user__username='test')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + auth_token.key)

        # dummy video addition
        video = self.createDummyVideo(workgroup_2.videolibrary)

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key('test')
            u.delete()
            User.objects.all().delete()

        except ObjectDoesNotExist:
            print("error in u delete")
            pass
        WorkGroup.objects.all().delete()
        Group.objects.all().delete()
        Video.objects.all().delete()

    def test_list_permissions_with_all_permissions(self):
        # give only the "change_workgroup" permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='view_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # assign perm
        assign_perm('view_workgroup', workgroup.group, workgroup_2)

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        list_permissions_url = url + "permissions/"

        response = self.client.get(list_permissions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_permissions_with_model_view_permission_without_object_view_permission(self):
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='view_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        list_permissions_url = url + "permissions/"

        response = self.client.get(list_permissions_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_permissions_to_workgroup_with_all_permission(self):
        # give only 'change_workgroup' permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='add_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')
        dummy_user = get_object_or_404(User, username="test_2")

        # assign perm
        assign_perm('view_workgroup', workgroup.group, workgroup_2)
        assign_perm('add_workgroup', workgroup.group, workgroup_2)

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        add_permission_url = url+"add_permission/"

        # codename
        data = {
            "codename": "view_tag"
        }

        response = self.client.post(add_permission_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(dummy_user.has_perm('tags.view_tag'))

    def test_add_permission_to_workgroup_without_add_permission_without_view_permission(self):
        workgroup = get_object_or_404(WorkGroup, name='test_group')

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')
        dummy_user = get_object_or_404(User, username="test_2")

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        add_permission_url = url+"add_permission/"

        data = {
            "codename" : "view_tag"
        }

        response = self.client.post(add_permission_url, data=data)
        self.assertFalse(dummy_user.has_perm("video.view_tag"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_add_permission_to_workgroup_without_add_permission_with_view_permission(self):
        workgroup = get_object_or_404(WorkGroup, name='test_group')

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')
        dummy_user = get_object_or_404(User, username="test_2")

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        add_permission_url = url+"add_permission/"

        data = {
            "codename" : "view_tag"
        }
        response = self.client.post(add_permission_url, data=data)
        self.assertFalse(dummy_user.has_perm("tags.view_tag"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_remove_permission_from_workgroup_with_all_permission(self):
        # give only 'add_workgroup' permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='add_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')
        dummy_user = get_object_or_404(User, username="test_2")

        # assign perm
        assign_perm('view_workgroup', workgroup.group, workgroup_2)
        assign_perm('add_workgroup', workgroup.group, workgroup_2)

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        remove_permission_url = url+"remove_permission/"

        # add permission to the group
        workgroup_2.group.permissions.add(get_object_or_404(Permission,codename='view_video'))

        data = {
            "codename" : "view_video"
        }

        response = self.client.post(remove_permission_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(dummy_user.has_perm('video.view_video'))

    def test_remove_permission_from_workgroup_without_add_permission_without_view_permission(self):
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # add permission to the group
        workgroup_2.group.permissions.add(get_object_or_404(Permission, codename='view_video'))

        # due to permission caching have to request after the assigning permission
        dummy_user = get_object_or_404(User, username="test_2")

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        remove_permission_url = url+"remove_permission/"

        data = {
            "codename": "view_video"
        }

        response = self.client.post(remove_permission_url, data=data)
        self.assertTrue(dummy_user.has_perm('video.view_video'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_remove_permission_from_workgroup_without_add_permission_with_view_permission(self):
        # give only the "view_workgroup" permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='view_workgroup'))
        assign_perm('view_workgroup', workgroup.group, workgroup)

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # add permission to the group
        # workgroup_2.group.permissions.add(get_object_or_404(Permission, codename='view_video'))
        assign_perm('video.view_video', workgroup_2.group)
        # due to permission caching have to request after the assigning permission
        dummy_user = get_object_or_404(User, username="test_2")

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk":str(workgroup_2.id)})
        remove_permission_url = url+"remove_permission/"

        data = {
            "codename": "view_video"
        }
        response = self.client.post(remove_permission_url, data=data)
        self.assertTrue(dummy_user.has_perm('video.view_video'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class WorkGroupVideoTests(APITestCase):
    test_dir = os.path.join(settings.BASE_DIR, 'tests')
    video_path = os.path.join(test_dir, 'test_video_upload/small_video.mp4')
    post_path = os.path.join(test_dir, 'test_video_upload/A_Day_In_The_Life.jpg')

    def createWorkGroup(self, name):
        group = Group.objects.create(name=str(uuid.uuid4()))
        videolibrary = VideoLibrary.objects.create()
        data = {"name": name}
        workgroup = WorkGroup.objects.create(group=group, videolibrary=videolibrary, **data)
        return workgroup

    def createDummyVideo(self, library):
        # post a video to video-list url
        url = reverse.reverse('video-list')

        data = {
            "title": "test_video",
            "file": open(self.video_path, 'rb'),
            "poster": open(self.post_path, 'rb')
        }
        self.client.post(url, data=data, format='multipart')
        video = get_object_or_404(Video, title='test_video')
        library.videos.add(video)
        return video

    def setUp(self):
        u = User.objects.create_user('test', password='test',
                                     email='test@test.test')
        u_2 = User.objects.create_user('test_2', password='test',
                                       email='test2@test.test')
        # create a workgroup for user
        workgroup = self.createWorkGroup('test_group')
        u.groups.add(workgroup.group)
        u.save()

        # dummy group
        workgroup_2 = self.createWorkGroup('test_group_2')
        u_2.groups.add(workgroup_2.group)
        u_2.save()

        assign_perm('video.add_video', workgroup.group)
        assign_perm('video.view_video', workgroup.group)

        # authorize the APIClient
        auth_token = Token.objects.get(user__username='test')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + auth_token.key)

        # dummy video addition
        video = self.createDummyVideo(workgroup_2.videolibrary)

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key('test')
            u.delete()
            User.objects.all().delete()

        except ObjectDoesNotExist:
            print("error in u delete")
            pass
        WorkGroup.objects.all().delete()
        Group.objects.all().delete()
        Video.objects.all().delete()

    def test_list_videos_with_all_permissions(self):
        # give only the "change_workgroup" permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='view_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # assign perm
        assign_perm('view_workgroup', workgroup.group, workgroup_2)

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        list_videos_url = url + "videos/"

        response = self.client.get(list_videos_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_videos_with_model_view_permission_without_object_view_permission(self):
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='view_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        list_videos_url = url + "videos/"

        response = self.client.get(list_videos_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_video_with_all_permission(self):
        # give only 'change_workgroup' permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='add_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # assign perm
        assign_perm('view_workgroup', workgroup.group, workgroup_2)
        assign_perm('add_workgroup', workgroup.group, workgroup_2)

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        upload_video_url = url + "upload_video/"

        test_dir = os.path.join(settings.BASE_DIR, 'tests')
        video_path = os.path.join(test_dir, 'test_video_upload/small_video.mp4')
        post_path = os.path.join(test_dir, 'test_video_upload/A_Day_In_The_Life.jpg')

        data = {
            "title": "A Day In The Life - The Beatles",
            "file": open(video_path, 'rb'),
            "poster": open(post_path, 'rb'),
        }
        response = self.client.post(upload_video_url, data=data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(workgroup_2.videolibrary.videos.all().count(), 2)

    def test_add_video_to_workgroup_with_all_permission(self):
        # give only 'change_workgroup' permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='add_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # assign perm
        assign_perm('view_workgroup', workgroup.group, workgroup_2)
        assign_perm('add_workgroup', workgroup.group, workgroup_2)

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        add_video_url = url + "add_video/"

        video = get_object_or_404(Video, title='test_video')

        data = {
            "id": video.id
        }

        response = self.client.post(add_video_url, data=data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(workgroup_2.videolibrary.videos.all().count(),2)

    def test_add_video_to_workgroup_without_add_permission_without_view_permission(self):
        workgroup = get_object_or_404(WorkGroup, name='test_group')

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        add_video_url = url + "add_video/"

        video = get_object_or_404(Video, title='test_video')

        data = {
            "id": video.id
        }

        response = self.client.post(add_video_url, data=data, format='multipart')
        self.assertEqual(workgroup_2.videolibrary.videos.all().count(), 1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_video_to_workgroup_without_add_permission_with_view_permission(self):
        workgroup = get_object_or_404(WorkGroup, name='test_group')

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        add_video_url = url + "add_video/"

        video = get_object_or_404(Video, title='test_video')

        data = {
            "id": video.id
        }

        response = self.client.post(add_video_url, data=data, format='multipart')
        self.assertEqual(workgroup_2.videolibrary.videos.all().count(), 1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_video_from_workgroup_with_all_permission(self):
        # give only 'add_workgroup' permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='add_workgroup'))

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # assign perm
        assign_perm('view_workgroup', workgroup.group, workgroup_2)
        assign_perm('add_workgroup', workgroup.group, workgroup_2)

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        remove_video_url = url + "remove_video/"

        video = get_object_or_404(Video,title='test_video')

        data = {
            "id": video.id
        }

        response = self.client.post(remove_video_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(workgroup_2.videolibrary.videos.all().count(), 0)

    def test_remove_video_from_workgroup_without_add_permission_without_view_permission(self):
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        remove_video_url = url + "remove_video/"

        video = get_object_or_404(Video, title='test_video')

        data = {
            "id": video.id
        }

        response = self.client.post(remove_video_url, data=data)
        self.assertEqual(workgroup_2.videolibrary.videos.all().count(), 1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_video_from_workgroup_without_add_permission_with_view_permission(self):
        # give only the "view_workgroup" permission
        workgroup = get_object_or_404(WorkGroup, name='test_group')
        workgroup.group.permissions.add(get_object_or_404(Permission, codename='view_workgroup'))
        assign_perm('view_workgroup', workgroup.group, workgroup)

        # dummy workgroup
        workgroup_2 = get_object_or_404(WorkGroup, name='test_group_2')

        # request and response
        url = reverse.reverse('workgroup-detail', kwargs={"pk": str(workgroup_2.id)})
        remove_video_url = url + "remove_video/"

        video = get_object_or_404(Video, title='test_video')

        data = {
            "id": video.id
        }

        response = self.client.post(remove_video_url, data=data)
        self.assertEqual(workgroup_2.videolibrary.videos.all().count(), 1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)





