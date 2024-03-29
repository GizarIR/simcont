import base64
import os
import unittest

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.signals import post_save
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

import logging

from users.models import CustomUser
from users.signals import send_activation_email

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


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_image


class BaseUserCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()

        cls.user_data = {
            "email": "test@example.com",
            "password": "testpassword",
            # "avatar": encode_image_to_base64(settings.MEDIA_URL + 'defaults/default_avatar.png')
        }

        post_save.disconnect(send_activation_email, sender=CustomUser)

        # Send POST request
        cls.create_response = cls.client.post('/users/register/', cls.user_data, format='json')
        cls.user = get_user_model().objects.get(email=cls.user_data['email'])

        # Activate user
        activation_data = {"activation_code": cls.user.activation_code}
        cls.activation_response = cls.client.post('/users/activate/', activation_data, format='json')

        # Login by JWT-token
        # Send post request for login
        cls.login_response = cls.client.post('/users/token/obtain/', cls.user_data, format='json')

        if cls.login_response.status_code != status.HTTP_200_OK:
            logger.info(f"Login failed. Response content: {cls.login_response.content}")

        # Check authentication
        access_token = cls.login_response.data['access']
        cls.authenticated_client = APIClient()
        cls.authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')


class RegistrationTestCase(BaseUserCase):
    @classmethod
    def setUpClass(cls):
        logger.info(f"***** Create test data for {cls.__name__} *****")
        super().setUpClass()

    def test_user_registration(self):
        logger.info(f"test_user_registration")

        # Check  (HTTP 201 Created)
        self.assertEqual(self.create_response.status_code, status.HTTP_201_CREATED)

        # Check create user
        self.assertEqual(self.user.email, "test@example.com")

        # Check activate (HTTP 200 OK)
        self.assertEqual(self.activation_response.status_code, status.HTTP_200_OK)

        # Check success login (HTTP 200 OK) and get JWT-token
        self.assertEqual(self.login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', self.login_response.data)
        self.assertIn('refresh', self.login_response.data)

    def test_get_profile(self):
        logger.info(f"test_get_profile")
        profile_response = self.authenticated_client.get('/users/profile/', format='json')
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['email'], 'test@example.com')

    def test_change_password(self):
        logger.info(f"test_change_password")
        password_data = {
            'old_password': self.user_data['password'],
            'new_password': "new_testpassword",
        }
        url = reverse('change_password')
        response = self.authenticated_client.post(url, password_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_profile(self):
        logger.info(f"test_put_profile")

        image_path = settings.MEDIA_ROOT + '/defaults/default_avatar.png'
        image_file = open(image_path, 'rb')
        image = SimpleUploadedFile(image_file.name, image_file.read())

        changing_data = {
            "email": self.user_data["email"],
            "avatar": image,
        }

        url = reverse('user_profile')
        response = self.authenticated_client.put(url, changing_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_profile(self):
        logger.info(f"test_patch_profile")

        image_path = settings.MEDIA_ROOT + '/defaults/default_avatar.png'
        image_file = open(image_path, 'rb')
        image = SimpleUploadedFile(image_file.name, image_file.read())

        changing_data = {
            "email": self.user_data["email"],
            "avatar": image,
        }

        url = reverse('user_profile')
        response = self.authenticated_client.put(url, changing_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_token(self):
        logger.info(f"test_refresh_token")
        changing_data = {
            "refresh": self.login_response.data['refresh'],
        }

        url = reverse('token_refresh')
        response = self.authenticated_client.post(url, changing_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['access'])


if __name__ == '__main__':
    unittest.main()
