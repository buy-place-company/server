"""
Django settings for buy_place_server project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from .settings_local import *

BASE_DIR = os.path.dirname(os.path.dirname(__file__) + "/../")
from .settings_local import *

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'm$_*es8ea$$k(u0%4)t&9sw^x#lexegxq6y2*@mw1(02rxt1%!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    # 'django.contrib.admin',
    #    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'django.contrib.messages',
    'django.contrib.staticfiles',
    'subsystems.db',
    'subsystems.foursquare',
    'subsystems.statistic',
    'subsystems.gcm',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    # 'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

ROOT_URLCONF = 'buy_place_server.urls'

WSGI_APPLICATION = 'buy_place_server.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR
STATICFILES_DIRS = (
    'static',
)

TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, 'templates')
]

# User
AUTH_USER_MODEL = 'db.User'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'localhost',
        'NAME': SettingsLocal.DB_NAME,
        'PORT': '6432',
        'USER': SettingsLocal.DB_USER,
        'PASSWORD': SettingsLocal.DB_PASSWORD
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'colored': {
            '()': 'buy_place_server.utils.DjangoColorsFormatter',
            'format': '%(levelname)s %(module)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored'
        },
        'null': {
            "class": 'django.utils.log.NullHandler',
        }

    },
    'loggers': {
        'django.request':{
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'subsystems.foursquare.api': {
            'handlers': ['console'],
            'level': "INFO",
        },
    },
}

from .secret import GCM_APIKEY