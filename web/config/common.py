#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
import os
from os.path import join

from configurations import Configuration
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_URL = os.getenv("BACKEND", '127.0.0.1')
FRONTEND_URL = os.getenv("FRONTEND", '127.0.0.1')

class Common(Configuration):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    DEBUG = False

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.postgres',

        # Third party apps
        'rest_framework',  # utilities for rest apis
        'rest_framework.authtoken',  # token authentication
        'rest_framework_simplejwt.token_blacklist',
        'versatileimagefield',  # image manipulation
        'storages',  # connect to gs
        'boto',  # connect to gs
        'djoser',
        'guardian',
        'corsheaders',
        'django_filters',
        'crispy_forms',
        'django_celery_results',
        'queued_storage',
        'nested_admin',
        'notifications',
        'thumbnails',
        'publication',
        'feedback',

        # testing
        'django_nose',

        # tracking
        'rest_framework_tracking',

        # debug
        # 'debug_toolbar',

        'rest_framework_docs',
        # 'django-database-size',

        # Your apps
        'authentication',
        'users',
        'video',
        'tags',
        'content',
        'workgroups',
        'jobs',
        'utils',
        'frames',
        'contextual',
        'permissions',
        'assets',
        'comments',
        'masters',
    )

    # https://docs.djangoproject.com/en/1.9/topics/http/middleware/
    MIDDLEWARE_CLASSES = (

        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    )

    ROOT_URLCONF = 'urls'

    SECRET_KEY = '*yYam3FI3M!i;`//ws|FRyeg+k*1wE=$b;2_[RT_J7:c0MH_hM'
    WSGI_APPLICATION = 'wsgi.application'

    # Authentication backend
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',  # this is default
        'django_python3_ldap.auth.LDAPBackend',
        'guardian.backends.ObjectPermissionBackend',  # guardian dependencies
    )

    SIMPLE_JWT = {
        "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=7)
    }

    # Email
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    # Email config
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_HOST_USER = 'apikey'
    EMAIL_HOST_PASSWORD = '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'
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
    DJOSER = {
        'DOMAIN': 'http://trigger-lite-dushyant.s3-website.ap-south-1.amazonaws.com',
        'SITE_NAME': 'Trigger',
        'PASSWORD_RESET_CONFIRM_URL': 'forgot-password/',
        'ACTIVATION_URL': 'auth/activate/{uid}/{token}',
        'SEND_ACTIVATION_EMAIL': True,
        'PASSWORD_VALIDATORS': [],
        'SERIALIZERS': {},
    }

    # Local db
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
            'DIRS': [os.path.join(BASE_DIR, 'templates')],
            'OPTIONS': {
                'context_processors': [
                    'django.contrib.auth.context_processors.auth',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.i18n',
                    'django.template.context_processors.media',
                    'django.template.context_processors.static',
                    'django.template.context_processors.request',
                    'django.template.context_processors.tz',
                    'django.contrib.messages.context_processors.messages'
                ],
                'loaders': [
                    ('django.template.loaders.cached.Loader', [
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                    ]),
                    # 'admin_tools.template_loaders.Loader',
                ],
            },
        },
    ]

    for config in TEMPLATES:
        config['OPTIONS']['debug'] = DEBUG

    # user model
    AUTH_USER_MODEL = 'users.User'

    # Django Rest Framework
    REST_FRAMEWORK = {
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': int(os.getenv('DJANGO_PAGINATION_LIMIT', 20)),
        'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
        'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ),
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
        # 'TEST_REQUEST_DEFAULT_FORMAT': 'json',
        'TEST_REQUEST_RENDERER_CLASSES': (
            'rest_framework.renderers.MultiPartRenderer',
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.TemplateHTMLRenderer'
        )
    }

    # # Session settings
    # SESSION_COOKIE_AGE = 60
    # SESSION_EXPIRE_AT_BROWSER_CLOSE = True

    # valid video types
    VIDEO_TYPES = ('mpeg', 'webm', 'ogg', 'mp4', 'mpg', '3gp')

    # valid image types
    IMG_TYPES = ('jpg', 'png', 'jpeg')

    # Django file storage in google cloud storage
    DEFAULT_FILE_STORAGE = 'storages.backends.gs.GSBotoStorage'
    GS_ACCESS_KEY_ID = 'GOOG5VDVLXFRMU27IHEX'
    GS_SECRET_ACCESS_KEY = '0ZFItM8qsVGR4p0mRDbilw33WBM+iI5SSQn+TtsO'
    GS_BUCKET_NAME = 'trigger-backend-media'

    # Static URL
    STATIC_URL = 'https://triggerbackendnormal.blob.core.windows.net/backend-static/static/'

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
            ('list_thumbnail', 'thumbnail__60x80'),
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
        ('ASG', 'Assigned'),
        ('PRD', 'Processed'),
        ('WIP', 'Work In Progress'),
        ('REV', 'Review'),
        ('QAP', 'Quality Assurance'),
        ('FAI', 'Job Failed')
    )

    LANGUAGES = (
        ('fr', 'French'),
        ('en', 'English'),
        ('pa', 'Punjabi'),
        ('hi', 'Hindi'),
        ('ta', 'Tamil'),
        ('mr', 'Marathi'),
        ('ml', 'Malayalam'),
        ('bn', 'Bengali')
    )

    # Django Debug Toolbar
    INTERNAL_IPS = [
        '127.0.0.1',
        '192.168.99.100'
    ]

    # drf extensions cache setting
    REST_FRAMEWORK_EXTENSIONS = {
        'DEFAULT_CACHE_RESPONSE_TIMEOUT': 20
    }

    # cors origin white list
    CORS_ORIGIN_WHITELIST = (
        'localhost:3000',
        'localhost:3000/',
        'localhost:3000/?',
        'tessact.vercel.app',
        'tessact.vercel.app/',
        'tessact.vercel.app/?',
        'trigger-timeline.vercel.app',
        'trigger-timeline.vercel.app/',
        'trigger-timeline.vercel.app/?',
        'localhost:3230',
        'localhost:3230/',
        'localhost:3230/?',
        'trigger-lite-dushyant.s3-website.ap-south-1.amazonaws.com',
        'trigger-lite-dushyant.s3-website.ap-south-1.amazonaws.com/',
        'trigger-lite-dushyant.s3-website.ap-south-1.amazonaws.com/?',
        'localhost:3230/?',
        'localhost:8000',
        'localhost:8000/?',
        '192.168.99.100',
        '127.0.0.1:8000',
        'localhost:3230',
        'localhost:3230/',
        'localhost:3230/?',
        BACKEND_URL,
        FRONTEND_URL

    )
    CSRF_TRUSTED_ORIGINS = (
        'localhost:3000',
        'localhost:3001',
        'localhost:3002',
        'localhost:8000',
        'localhost:8000/?',
        '127.0.0.1:8000',
        'tessact.vercel.app',
        'trigger-timeline.vercel.app',
        'trigger-lite-dushyant.s3-website.ap-south-1.amazonaws.com',
        'localhost:3230',
        BACKEND_URL,
        FRONTEND_URL
    )

    CORS_ALLOW_CREDENTIALS = True

    CORS_ORIGIN_REGEX_WHITELIST = (r'^(https?://)?(\w+\.)?localhost:3000$',
                                   r'^(https?://)?(\w+\.)?localhost:3001$',
                                   r'^(https?://)?(\w+\.)?localhost:3002$',
                                   r'^(https?://)?(\w+\.)?localhost:3003$',
                                   r'^(https?://)?(\w+\.)?localhost:5000$',
                                   r'^(https?://)?(\w+\.)?localhost:4200$',
                                   r'^(https?://)?(\w+\.)?localhost:8000$',
                                   r'^(https?://)?(\w+\.)?trigger-timeline.vercel.app$',
                                   r'^(https?://)?(\w+\.)?tessact.vercel.app$',
                                   r'^(http?://)?(\w+\.)?tessact.vercel.app$',
                                   r'^(https?://)?(\w+\.)?localhost:3230$',
                                   r'^(https?://)?(\w+\.)?trigger-lite-dushyant.s3-website.ap-south-1.amazonaws.com$',
                                   r'^(https?://)?(\w+\.)?127.0.0.1$',
                                   r'^(https?://)?(\w+\.)?{}$'.format(BACKEND_URL),
                                   r'^(https?://)?(\w+\.)?{}$'.format(FRONTEND_URL)
                                   )

    # You have 'django.middleware.clickjacking.XFrameOptionsMiddleware' in your MIDDLEWARE_CLASSES, but
    # X_FRAME_OPTIONS is not set to 'DENY'.The default is 'SAMEORIGIN', but unless there is a good reason
    # for your site to serve other parts of itself in a frame, you should change it to 'DENY'
    # X_FRAME_OPTIONS = 'DENY'

    # You have 'django.middleware.csrf.CsrfViewMiddleware' in your MIDDLEWARE_CLASSES, but
    # you have not set CSRF_COOKIE_HTTPONLY to True. Using an HttpOnly CSRF cookie makes it more difficult
    # for cross - site scripting attacks to steal the CSRF token
    # CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = False

    beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
    DJANGO_NOTIFICATIONS_CONFIG = { 'USE_JSONFIELD': True}
    CORS_ORIGIN_ALLOW_ALL = True

