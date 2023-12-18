# TBC Membership App
One stop shop for all of Tech by Choice site

##Requirements
Python 3.8.0

#Getting Started 
This is a monorepo containing both a Django Rest Framework backend and a React frontend.
## Structure
```
/tbc-membership
/api
/apps
/templates
.example-env
.gitignore
Procfile
manage.py
requirements.txt
/frontend
/public
/src
package.json
## Backend 
```

## Backend Setup (Django & DRF)

1. In your terminal navigate to the `api` folder
    ```
       $ cd tbc/api
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