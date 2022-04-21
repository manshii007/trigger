#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
import os
from os.path import join


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',


    # Third party apps
    'rest_framework',            # utilities for rest apis
    'rest_framework.authtoken',  # token authentication
    'django_rq',                 # asynchronous queuing
    'versatileimagefield',       # image manipulation
    'storages',                  # connect to gs
    'boto',                      # connect to gs
    'djoser',                    # user end points
    'guardian',                  # object permissions

    # Your apps
    'authentication',
    'users',
    'video',
    'tags',
    'content',
    'workgroups',
    'jobs',
    'thumbnails',

    # debug
    'debug_toolbar'

)

# https://docs.djangoproject.com/en/1.9/topics/http/middleware/
MIDDLEWARE_CLASSES = (
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

)

ROOT_URLCONF = 'urls'

SECRET_KEY = os.getenv('SECRET_KEY')
WSGI_APPLICATION = 'wsgi.application'

# Authentication backend
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # this is default
    'guardian.backends.ObjectPermissionBackend',  # guardian dependencies
)

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Email config
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'priyatham'
EMAIL_HOST_PASSWORD = 'drake is cool123'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

DJOSER = {
    'DOMAIN': 'trigger-backend.appspot.com',
    'SITE_NAME': 'Trigger',
    'PASSWORD_RESET_CONFIRM_URL': '#/password/reset/confirm/{uid}/{token}',
    'ACTIVATION_URL': '#/activate/{uid}/{token}',
    'SEND_ACTIVATION_EMAIL': True,
    'PASSWORD_VALIDATORS': [],
    'SERIALIZERS': {},
}

ADMINS = (
    ('Author', 'aswin@tessact.com'),
)


db_config = os.environ.get('DB_CONFIGURATION')
if db_config == 'Production':
    # Postgres
    DATABASES = {
        'default' : {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST'),
            'PORT': os.environ.get('DB_PORT'),
        }
    }
    # Cache
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://:A1MuNeTn@104.154.113.28:6379/0",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            }
        }
    }

    EMAIL_PORT = 2525
elif db_config == 'Migrate':
    # Postgres
    DATABASES = {
        'default' : {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_EX_HOST'),
            'PORT': os.environ.get('DB_PORT'),
        }
    }
    # Cache
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://:A1MuNeTn@104.154.113.28:6379/0",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            }
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
elif db_config == 'Compose':
    # Postgres
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'postgres',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'postgres',
            'PORT': os.environ.get('DB_PORT'),
        }
    }
elif db_config == 'Container':
    #
    # Not used anymore
    #
    DJANGO_PW = os.getenv('DJANGO_PASSWORD')
    if not DJANGO_PW:
        try:
            f = open('/etc/secrets/djangouserpw')
            DJANGO_PW = f.readline().rstrip()
        except IOError:
            pass
    if not DJANGO_PW:
        raise Exception("No DJANGO_PASSWORD provided.")

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'triggerdb',
            'USER': 'adminuser',
            'PASSWORD': DJANGO_PW,
            'HOST': os.getenv('POSTGRES_SERVICE_HOST', '127.0.0.1'),
            'PORT': os.getenv('POSTGRES_SERVICE_PORT', 5432)
        }
    }
    # CACHES
    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': [
                '%s:%s' % (os.getenv('REDIS_MASTER_SERVICE_HOST', '127.0.0.1'),
                           os.getenv('REDIS_MASTER_SERVICE_PORT', 6379)),
                '%s:%s' % (os.getenv('REDIS_SLAVE_SERVICE_HOST', '127.0.0.1'),
                           os.getenv('REDIS_SLAVE_SERVICE_PORT', 6379))
            ],
            'OPTIONS': {
                'PARSER_CLASS': 'redis.connection.HiredisParser',
                'PICKLE_VERSION': 2,
                'MASTER_CACHE': '%s:%s' % (
                    os.getenv('REDIS_MASTER_SERVICE_HOST', '127.0.0.1')
                    , os.getenv('REDIS_MASTER_SERVICE_PORT', 6379))
            },
        },
    }
    # LOGGING
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': '/app/debug.log',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': join(BASE_DIR, 'db.sqlite3'),
        }
    }

# General
APPEND_SLASH = True

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False
USE_L10N = True
USE_TZ = True
LOGIN_REDIRECT_URL = '/'

# Static Files
STATIC_ROOT = join(BASE_DIR, 'staticfiles')
# STATICFILES_DIRS = (join(BASE_DIR, 'staticfiles'),)
# STATIC_URL = '/static/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Local media files
MEDIA_ROOT = join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages'
            ],
            'loaders':[
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]

# Set DEBUG to False as a default for safety
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True

for config in TEMPLATES:
    config['OPTIONS']['debug'] = DEBUG

# user model
AUTH_USER_MODEL = 'users.User'

# Django Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': int(os.getenv('DJANGO_PAGINATION_LIMIT', 10)),
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    )
}

# django-rq
# Adds dashboard link for queues in /admin, This will override the default
# admin template so it may interfere with other apps that modify the
# default admin template. If you're using such an app, simply remove this.
RQ_SHOW_ADMIN_LINK = True

# valid video types
VIDEO_TYPES = ('mpeg', 'webm', 'ogg', 'mp4', 'mpg', '3gp')

# valid image types
IMG_TYPES = ('jpg', 'png', 'jpeg')

# Django file storage in google cloud storage
DEFAULT_FILE_STORAGE = 'storages.backends.gs.GSBotoStorage'
GS_ACCESS_KEY_ID = os.getenv('GS_ACCESS_KEY_ID')
GS_SECRET_ACCESS_KEY = os.getenv('GS_SECRET_ACCESS_KEY')
GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME')

# Static URL
STATIC_URL = os.getenv('STATIC_URL')

# Django RQ settings
RQ_QUEUES = {
    'default': {
        'URL': os.getenv('REDISTOGO_URL', 'redis://localhost:6379'),
        'DB': 0,
        'DEFAULT_TIMEOUT': 500,
    },
}

# Versatile Image Field
VERSATILEIMAGEFIELD_SETTINGS = {
    # The amount of time, in seconds, that references to created images
    # should be stored in the cache. Defaults to `2592000` (30 days)
    'cache_length': 2592000,
    'cache_name': 'versatileimagefield_cache',
    'jpeg_resize_quality': 70,
    'sized_directory_name': '__sized__',
    'filtered_directory_name': '__filtered__',
    'placeholder_directory_name': '__placeholder__',
    'create_images_on_demand': False
}

# Rendition types for central control
VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'video_poster': [
        ('full_size', 'url'),
        ('thumbnail', 'thumbnail__100x100'),
        ('medium_square_crop', 'crop__400x400'),
        ('small_square_crop', 'crop__50x50')
    ]
}

# status choice
JOB_STATUS = (
    ('APR', 'Approved'),
    ('REJ', 'Rejected'),
    ('PRO', 'Processing'),
    ('NPR', 'Not Processed'),
    ('EDT', 'Edit Required'),
    ('ASG', 'Assigned')
)

# internal ip for debug toolbar
INTERNAL_IPS = [
    '127.0.0.1'
]

# toolbar panels
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

# drf extensions cache setting
REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60
}