web: celery -A api worker --loglevel=info &python manage.py migrate && gunicorn api.wsgi --bind 0.0.0.0:$PORT
