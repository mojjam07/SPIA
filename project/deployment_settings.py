"""
Deployment settings for project.

This file imports all settings from the base development settings (project.settings)
and overrides necessary settings for production deployment.
"""

import os
from project.settings import *  # Import base settings

import dj_database_url

# Override SECRET_KEY to use environment variable
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)

# Set DEBUG to False by default, can be overridden by environment variable
DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 't']

# Set ALLOWED_HOSTS from environment variable, default empty list
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Configure DATABASES to use DATABASE_URL environment variable if present
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
# else keep the DATABASES from base settings (likely SQLite)

# Additional production security settings can be added here if needed
# For example:
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
