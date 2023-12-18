import pytest
from rest_framework.test import APIClient

client = APIClient()


@pytest.mark.django_db
def test_register_user():
    payload = dict(
        first_name='linda',
        last_name='Burger',
        password='ilovemyFamily!',
        email='Linda@burgers.com',
        username='Linda',
    )

    response = client.post('/user/register', payload)
    data = response
    assert data['first_name'] == payload['first_name']
