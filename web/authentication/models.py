#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.db import models
import uuid

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class AuthOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    otp = models.CharField(max_length=8)
    sent_time = models.DateTimeField(auto_now_add=True, null=True)
    threshold = models.IntegerField(default=180, null=False)

@receiver(post_save, sender=AuthOTP)
def send_otp(sender, instance=None, created=False, **kwargs):
    if created:
        user = instance.user
        if user.email and instance.otp:
            # send email
            send_mail(
                "Your OTP for Sony YAY Analytics",
                " Please find the OTP here \n OTP : {}".format(instance.otp),
                'trigger@setindia.com',
                [user.email],
                fail_silently=False,
            )
