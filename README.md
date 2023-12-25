# TBC Membership App
One stop shop for all of Tech by Choice site

##Requirements
Python 3.8.0

#Getting Started 
This is a repo containing both a Django Rest Framework backend and a React frontend.
## Structure
```
.
├── api
│   ├── asgi.py
│   ├── celery.py
│   ├── settings.py
│   ├── storage_backends.py
│   ├── urls.py
│   └── wsgi.py
├── apps
│   ├── company
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── management
│   │   │   └── commands
│   │   │       └── import_lever_jobs.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── task.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── views_accounts.py
│   │   └── views_jobs.py
│   ├── core
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── serializers_member.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   ├── urls_member.py
│   │   ├── views.py
│   │   └── views_member.py
│   ├── event
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── mentorship
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializer.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   └── talent
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── serializers.py
│       ├── tests.py
│       └── views.py
├── Pipfile
├── Pipfile.lock
├── Procfile
├── README.md
├── example.env
├── manage.py
├── pytest.ini
├── requirements.txt

## Backend Setup (Django & DRF)

1. In your terminal navigate to the `api` folder
    ```
       $ cd tbc/tbc-members-core-api
    ```   
2. Create the virtual environment:
    ```
       $ python3 -m venv venv
    ```
3. Activate the virtual environment:

    For Unix-based systems (aka a mac)
    ```
       $ source venv/bin/activate
    ```
   For Windows
    ```
       $ .\venv\Scripts\activate
    ```   
4. Install the all of the library needed to run the app 
    ```
       $ pip install -r requirements.txt
    ```
5. Start the app
    ```
       $ python manage.py runserver
    ```