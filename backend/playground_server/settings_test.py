from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

import os
from cryptography.fernet import Fernet
os.environ.setdefault('MNEMONIC_ENCRYPTION_KEY', Fernet.generate_key().decode())

LOGGING = {}
