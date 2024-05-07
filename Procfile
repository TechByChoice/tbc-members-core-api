web: celery -A api worker --loglevel=info &python manage.py migrate && gunicorn api.wsgi
