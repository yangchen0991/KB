"""
WSGI config for knowledge_base project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "knowledge_base.settings")

application = get_wsgi_application()
