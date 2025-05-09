from pathlib import Path
import os
import dj_database_url
from decouple import config

# # Add this to check if the config function is working
# try:
#     test_var = config('SECRET_KEY', default='ENV_NOT_WORKING')
#     print(f"Config function is working. SECRET_KEY starts with: {test_var[:5]}...")
# except Exception as e:
#     print(f"Error with config function: {e}")



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = config('SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

CSRF_TRUSTED_ORIGINS = [
        'https://micro-foodbank-backend-44tkf.kinsta.app',
        'https://baker-production.up.railway.app',
        # Keep any existing origins
        ]

ALLOWED_HOSTS = [
        '127.0.0.1',
        'localhost',
        '68.183.152.209',
        'bakery-projectbe-6q46.onrender.com',
        'baker-production.up.railway.app'
        ]



# Application definition

INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        # THIRD PARTY APP
        'drf_yasg',

        'rest_framework',



        # LOCAL APP

        'products.apps.ProductsConfig',

        'cart.apps.CartConfig',

        'orders.apps.OrdersConfig',

        'payment.apps.PaymentConfig',

        ]

MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]

ROOT_URLCONF = 'bake_world.urls'

TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'cart.context_processors.cart',
                    ],
                },
            },
        ]

WSGI_APPLICATION = 'bake_world.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
  #  'default': {
   #     'ENGINE': 'django.db.backends.sqlite3',
    #    'NAME': BASE_DIR / 'db.sqlite3',
   # }
 # }

# Check if we're running on Render (production)
IS_RENDER = config('IS_RENDER', default=False, cast=bool)

# Database configuration based on environment
if IS_RENDER:
    # Use Render PostgreSQL database in production
    DATABASES = {
            'default': dj_database_url.config(
                default=config('DATABASE_URL'),
                conn_max_age=600
                )
            }
else:
    # Use SQLite for local development
    DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
                }
            }
    # Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
            },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
            },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
            },
        ]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'


# if not DEBUG:
    # Tell Django to copy static assets into a path called `staticfiles` (this is specific to Render)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # Enable the WhiteNoise storage backend, which compresses static files to reduce disk use
    # and renames the files with unique names for each version to support long-term caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


# CREATING SHOPPING CART SESSION
CART_SESSION_ID = 'cart'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# PAYMENT GATEWAY SETUP
#PAYSTACK_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY')
#PAYSTACK_SECRET_KEY = config('STRIPE_SECRET_KEY')
#PAYSTACK_API_VERSION = '2025-01-24'


try:
    PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY')
    PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY')
except Exception as e:
    print("Error loading Paystack keys:", e)
