import os

from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model


import logging
if 'DJANGO_SETTINGS_MODULE' in os.environ:
    # if Django start
    from django.conf import settings
else:
    # else console start
    import logging.config
    from simcont import settings
    logging.config.dictConfig(settings.LOGGING)

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


class RegistrationTestCase(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        logger.info(f"test_user_registration")
        user_data = {
            "email": "test@example.com",
            "password": "testpassword",
        }

        # Send POST request
        response = self.client.post('/users/register/', user_data, format='json')

        # Check  (HTTP 201 Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check create user
        self.assertTrue(get_user_model().objects.filter(email=user_data['email']).exists())

        # Get user from DB
        user = get_user_model().objects.get(email=user_data['email'])

        # Get activation code
        activation_code = user.activation_code

        # Activate user
        activation_data = {"activation_code": activation_code}
        activation_response = self.client.post('/users/activate/', activation_data, format='json')

        # Check activate (HTTP 200 OK)
        self.assertEqual(activation_response.status_code, status.HTTP_200_OK)

        # Login by JWT-token
        login_data = {
            "email": user_data['email'],
            "password": user_data['password'],
        }
        # Send post request for login
        login_response = self.client.post('/users/token/obtain/', login_data, format='json')

        if login_response.status_code != status.HTTP_200_OK:
            logger.info(f"Login failed. Response content: {login_response.content}")

        # Check success login (HTTP 200 OK) and get JWT-token
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)

        # Check authentication
        access_token = login_response.data['access']
        authenticated_client = APIClient()
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Example for check
        profile_response = authenticated_client.get('/users/profile/', format='json')

        # Check success result (HTTP 200 OK)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
