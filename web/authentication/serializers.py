from rest_framework import serializers
from .models import AuthOTP
from users.models import User
from datetime import datetime, timezone
from  rest_framework.exceptions import AuthenticationFailed

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        request = self.context["request"]
        username = request.data.get("username")
        user = User.objects.get(username=username)
        days_since_joined = (datetime.now(timezone.utc) - user.date_joined).days
        if days_since_joined > 7:
            if user.is_demo:
                raise AuthenticationFailed("please upgrade to paid plan", "demo_expired")
        return data

class MyTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        request = self.context["request"]
        return data

class AuthOTPSerializers(serializers.ModelSerializer):

    class Meta:
        model = AuthOTP
        fields = '__all__'

class SimpleAuthOTPSerializers(serializers.ModelSerializer):

    class Meta:
        model = AuthOTP
        fields = ('id', 'user')
