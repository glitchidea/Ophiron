#!/bin/sh
set -e

# Apply database migrations
python manage.py migrate --noinput

# Ensure default admin user exists (admin/admin) - for local/dev use
# Use manage.py shell so Django is initialized properly; never fail startup
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); u=User.objects.filter(username='admin').first();\n\nif not u:\n    User.objects.create_superuser(username='admin', email='admin@example.com', password='admin');\n    print('Created default superuser: admin/admin')\nelse:\n    print('Default superuser already exists')" || true

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
