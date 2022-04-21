#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from .common import Common
import os
try:
    # Python 2.x
    import urlparse
except ImportError:
    # Python 3.x
    from urllib import parse as urlparse


class Container(Common):
    # DEBUG = os.getenv('DEBUG',False)
    DEBUG = True
    INSTALLED_APPS = Common.INSTALLED_APPS

    # secure settings when using https
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # SECURE_HSTS_SECONDS = 60
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_FRAME_DENY =True
    # SECURE_CONTENT_TYPE_NOSNIFF = True
    # SECURE_BROWSER_XSS_FILTER = True
    # SESSION_COOKIE_SECURE = True
    # SECURE_SSL_REDIRECT = False

    ALLOWED_HOSTS = ["*"]

    INSTALLED_APPS += ("gunicorn",)

    # db
    # Postgres
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'postgres',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': '3.110.205.43',
            'PORT': '5432',
        }
    }
    # Cache
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://redis:6379",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            }
        }
    }

    # Logging
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            },
            'debug': {
                'handlers': ['console'],
                'level': 'DEBUG'
            },
        },
    }

    # DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    DEFAULT_FILE_STORAGE = 'utils.azure_storage.AzureStorage'

    # Azure storage
    AZURE_ACCOUNT_NAME='triggerbackendnormal'
    AZURE_ACCOUNT_KEY='tadQP8+aFdnxzHBx37KYLoIV92H+Ju9U7a+k1qtwaQDE0tH23qQ7mUUD1qzvXBGd6cGgo7rW4jeA8H6AzXZdPg=='
    AZURE_CONTAINER='backend-media'

    # Celery settings
    CELERY_BROKER_URL = "amqp://adminuser:adminuser@rabbitmq:5672/myvhost"
    CELERY_IMPORTS = ['video.tasks', 'trigger.celery', 'content.tasks']
    CELERY_RESULT_BACKEND = 'django-db'

    # Celery queues setup
    CELERY_BEAT_SCHEDULE = {
        'run-every-five-minutes': {
            'task': 'update_process_status',
            # There are 4 ways we can handle time, read further
            'schedule': 60.0*5,
            # If you're using any arguments
            'args': ('none',),
        },
        'run-every-ten-minutes':{
        'task': 'update_batch',
            # There are 4 ways we can handle time, read further
            'schedule': 60.0*10,
            # If you're using any arguments
            'args': ('none',),
        },
        'run-every-day': {
        'task': 'periodic_video_indexing',
        # There are 4 ways we can handle time, read further
        'schedule': 60.0*1440,
        # If you're using any arguments
        'args': ('none',),
        }
    }

    EMAIL_PORT = 2525

    CORS_REPLACE_HTTPS_REFERER = True
