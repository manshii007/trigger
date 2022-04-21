#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from __future__ import unicode_literals

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.encoding import python_2_unicode_compatible
from utils.unique_filename import unique_upload
from .validator import validate_img_file_type



@python_2_unicode_compatible
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    forgot_password_token = models.CharField(max_length=128, null=True)
    recent_search = models.TextField(null=True)
    is_demo =  models.BooleanField(default=True)
    AbstractUser._meta.get_field('email')._unique = True
    AbstractUser._meta.get_field('email')._blank = False

    def __str__(self):
        return self.first_name+" "+self.last_name

    class Meta:
        permissions = (('view_user', 'Can view user'),)


class Profile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User,on_delete = models.CASCADE, related_name='profile')
    profile_picture = models.FileField(upload_to=unique_upload, max_length=None, validators=[validate_img_file_type])
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(choices=GENDER_CHOICES, blank=False, max_length=2)
    secondary_email = models.EmailField(blank=True)
    Address = models.TextField(blank=True, null=True)

    class Meta:
        permissions = (('view_profile', 'Can view profile'),)
