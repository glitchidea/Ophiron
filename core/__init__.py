"""
Core Package Initialization
"""

# Celery app'i import et (Django başlarken Celery de başlasın)
from .celery import app as celery_app

__all__ = ('celery_app',)

