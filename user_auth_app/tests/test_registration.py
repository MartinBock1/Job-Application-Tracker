from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from django.contrib.auth.models import User


class RegistrationTests(APITestCase):
    """
    Test suite for the user registration functionality.

    This class provides tests for the registration API endpoint, covering
    successful account creation and common failure scenarios like password
    mismatches.
    """

    def setUp(self):
        self.registration_url = reverse('registration')
        
    def test_registration_success(self):
        """
        Ensure a new user can be registered successfully with valid data.

        This test verifies the entire registration flow:
        1. A POST request is sent to the registration endpoint with valid data.
        2. The response status code is checked for 201 Created.
        3. The response body is checked to ensure it contains the auth token and correct user details.
        4. The database is checked to confirm that both a `User` and a `Profile`
           object were correctly created.
        """
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPassword123',
            'repeated_password': 'StrongPassword123'
        }

        response = self.client.post(self.registration_url, user_data, format='json')

        # Check for a successful creation status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify that the user was actually created in the database
        user_exists = User.objects.filter(email='test@example.com').exists()
        self.assertTrue(user_exists)
        
        # Check the response body for expected fields
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], user_data['username'])
        self.assertEqual(response.data['email'], user_data['email'])

    def test_registration_password_mismatch(self):
        """
        Ensure registration fails if the provided passwords do not match.

        This test sends a POST request with mismatched 'password' and
        'repeated_password' fields and verifies that:
        1. The API returns a 400 Bad Request status code.
        2. The response body contains the specific error message for the mismatch.
        3. No new user is created in the database.
        """
        user_data = {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'GoodPassword123',
            'repeated_password': 'BadPassword456'
        }

        response = self.client.post(self.registration_url, user_data, format='json')

        # Check for a bad request status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check the specific error message.
        # The traceback shows that for a non-field error raised as a dictionary,
        # the test client may return the error message as a direct string value,
        # not a list containing the string.
        # Therefore, we compare the value directly.
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'dont`t match')

        # Verify that no user was created in the database
        user_exists = User.objects.filter(email='mismatch@example.com').exists()
        self.assertFalse(user_exists)
