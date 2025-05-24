import environ
from .settings import *

env = environ.Env(
    DEBUG=(bool, False)
)

# reading .env file
environ.Env.read_env()

DEBUG = env('DEBUG')

PORT = os.environ.get('PORT', '8000')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['spia.onrender.com', 'www.stockpilot.com'])

SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)

SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)

SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=True)

STATIC_ROOT = BASE_DIR / 'staticfiles'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='your_db_name'),
        'USER': env('DB_USER', default='your_db_user'),
        'PASSWORD': env('DB_PASSWORD', default='your_db_password'),
        'HOST': env('DB_HOST', default='your_db_host'),
        'PORT': env('DB_PORT', default='your_db_port'),
    }
}

SECURE_BROWSER_XSS_FILTER = env.bool('SECURE_BROWSER_XSS_FILTER', default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool('SECURE_CONTENT_TYPE_NOSNIFF', default=True)

EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.your-email-provider.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='your-email@example.com')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='your-email-password')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
