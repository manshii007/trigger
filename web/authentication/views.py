from rest_framework import viewsets, status
from .serializers import AuthOTPSerializers, SimpleAuthOTPSerializers, MyTokenObtainPairSerializer, MyTokenRefreshSerializer
from .models import AuthOTP
from random import randint
from rest_framework.decorators import list_route
from rest_framework.response import Response
import datetime
from django.utils import timezone

from rest_framework_simplejwt.views import TokenViewBase

class TokenObtainPairView(TokenViewBase):
    serializer_class = MyTokenObtainPairSerializer

class TokenRefreshView(TokenViewBase):
    serializer_class = MyTokenRefreshSerializer

def expires_in(sent_time, threshold):
    time_elapsed = timezone.now() - sent_time
    left_time = datetime.timedelta(seconds=threshold) - time_elapsed
    return left_time

class AuthOTPViewSet(viewsets.ModelViewSet):
    serializer_class = AuthOTPSerializers
    queryset = AuthOTP.objects.all()

    def create(self, request, *args, **kwargs):
        auth_object = AuthOTP.objects.create(user=request.user, otp=randint(10000000, 99999999), threshold=180)
        if auth_object:
            otp_model = SimpleAuthOTPSerializers(auth_object)
            return Response(otp_model.data, status=status.HTTP_200_OK)
        else:
            return Response(data={"msg":"OTP cannot be created"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_queryset(self):
        return AuthOTP.objects.all().filter(user=self.request.user).order_by("-sent_time")

    @list_route(methods=["post"])
    def check_otp(self, request):
        last_otp = self.get_queryset().first()
        current_otp = request.data.get("otp", None)
        left_time = expires_in(last_otp.sent_time, last_otp.threshold)
        if current_otp and last_otp and last_otp.otp==current_otp and left_time > datetime.timedelta(seconds=0):
            return Response(data={"msg":"OTP is validated"}, status=status.HTTP_200_OK)
        else:
            return Response(data={"msg": "OTP is wrong"}, status=status.HTTP_417_EXPECTATION_FAILED)
