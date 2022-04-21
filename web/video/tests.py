#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework import (
    status,
    reverse,
)
from rest_framework.authtoken.models import Token

from django.core.exceptions import ObjectDoesNotExist

import os

from users.models import User

from .models import Video


class VideoTests(APITestCase):

    def setUp(self):
        self.tearDown()
        u = User.objects.create_user('test', password='test',
                                     email='test@test.test')
        u.save()

    def tearDown(self):
        try:
            u = User.objects.get_by_natural_key('test')
            u.delete()

        except ObjectDoesNotExist:
            pass
        Video.objects.all().delete()

    def test_video_upload(self):
        """
        Ensure we can create a new video object
        """
        url = reverse.reverse('video-list')
        test_dir = os.path.join(settings.BASE_DIR, 'tests')
        post_path = os.path.join(test_dir, 'test_video_upload/A_Day_In_The_Life.jpg')

        data = {
            "title": "A Day In The Life - The Beatles",
            "file": "https://triggerbackendnormal.blob.core.windows.net/backend-media/Who%20Blessed%20This%20For%2013%20Years%20-%20The%20Newshour%20Debate%20(10th%20May).mp4",
            "poster": open(post_path, 'rb')
        }

        token = Token.objects.get(user__username='test')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Video.objects.count(), 1)
        self.assertEqual(Video.objects.get().title, 'A Day In The Life - The Beatles')
