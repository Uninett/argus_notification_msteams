SECRET_KEY = 'stuffandnonsense'

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

AUTH_USER_MODEL = "argus_auth.User"

USE_TZ = True

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',

    # Must make tables
    'argus.auth',
    'argus.incident',
    'argus.notificationprofile',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

MIDDLEWARE_CLASSES = ()

# Argus specific settings
NOTIFICATION_SUBJECT_PREFIX = "[Argus] "
MEDIA_PLUGINS = [
    "argusnotification.msteams.MSTeamsNotification",
]
