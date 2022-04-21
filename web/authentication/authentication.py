from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
import datetime
from django.utils import timezone

from rest_framework.exceptions import (AuthenticationFailed, APIException,)
import logging, sys

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO'
    }
}
logging.config.dictConfig(LOGGING)

#this return left time
def expires_in(token):
    time_elapsed = timezone.now() - token.created
    left_time = datetime.timedelta(seconds = 30*60) - time_elapsed
    return left_time

# token checker if token expired or not
def is_token_expired(token):
    return expires_in(token) < datetime.timedelta(seconds = 0)

# if token is expired new token will be established
# If token is expired then it will be removed
# and new one with different key will be created
def token_expire_handler(token):
    is_expired = is_token_expired(token)
    if is_expired:
        token.delete()
    return is_expired

class SessionTimedOut(APIException):
    status_code = 599
    default_detail = 'Session timed out, please login again!'
    default_code = 'service_unavailable'


class CustomTokenAuthentication(TokenAuthentication):

    def authenticate_credentials(self, key):
        try:
            token = Token.objects.get(key = key)
            is_expired = token_expire_handler(token)
            if is_expired:
                logging.info("here")
                raise SessionTimedOut()
        except Token.DoesNotExist:
            logging.info("there")
            raise AuthenticationFailed("Invalid Token")
        
        if not token.user.is_active:
            raise AuthenticationFailed("User is inactive")
        
        return (token.user, token)