# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
import os

INSTALLED_APPS = ['life', 'pushes', 'mbdb', 'l10nstats']

MAX_HG_RETRIES = 5  # retry HG worker tasks 5 times

# load configs from a local.py file
try:
    from .local import *  # noqa
except ImportError:
    pass

# overload configuration from environment, as far as we have it
try:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ['ELMO_DB_NAME'],
            'USER': os.environ['ELMO_DB_USER'],
            'PASSWORD': os.environ['ELMO_DB_PASSWORD'],
            'HOST': os.environ['ELMO_DB_HOST'],
            'PORT': '',
            'CONN_MAX_AGE': 500,
            'OPTIONS': {
                'charset': 'utf8',
                'use_unicode': True,
            },
            'TEST': {
                'CHARSET': "utf8",
                'COLLATION': 'utf8_general_ci',
            },
        },
    }
except KeyError:
    pass
for local_var, env_var in (
            ('SECRET_KEY', 'ELMO_SECRET_KEY'),
            ('REPOSITORY_BASE', 'ELMO_REPOSITORY_BASE'),
            ('TRANSPORT', 'ELMO_TRANSPORT'),
):
    if env_var in os.environ:
        locals()[local_var] = os.environ[env_var]

if 'ELMO_SENTRY_DSN' in os.environ:
    RAVEN_CONFIG = {
        'dsn': os.environ['ELMO_SENTRY_DSN']
    }
