from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User


class LoginTests(APITestCase):
    """
    Test suite for the user login functionality.

    This class contains tests that cover various scenarios for the login API
    endpoint, including successful authentication, failed attempts with bad
    credentials, and requests with missing data.
    """

    def setUp(self):
        """
        Set up the test environment before each test method is run.

        This method creates a standard user in the test database, which will be
        used to test the login process.
        """
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='exampleUsername',
            email='example@mail.de',
            password='examplePassword'
        )

    def test_login_success(self):
        """
        Ensure a registered user can successfully log in with correct credentials.

        This test sends a POST request with a valid email and password to the
        login endpoint. It verifies that the response has a 200 OK status code
        and contains the expected data: an authentication token and user details.
        """
        data = {
            "email": "example@mail.de",
            "password": "examplePassword"
        }
        response = self.client.post(self.login_url, data, format='json')

        # Assert that the request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that the response contains the expected keys and values
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'exampleUsername')
        self.assertEqual(response.data['email'], 'example@mail.de')

    def test_login_bad_credentials(self):
        """
        Ensure a login attempt with incorrect credentials fails.

        This test sends a POST request with a valid email but an incorrect password. It
        verifies that the response has a 400 Bad Request status code and contains the
        specific non-field error message indicating an authentication failure.
        """
        data = {
            "email": "example@mail.de",
            "password": "wrongPassword"
        }
        response = self.client.post(self.login_url, data, format='json')

        # Assert that the request was a bad request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        expected_error = "Invalid email or password."
        self.assertEqual(str(response.data['non_field_errors'][0]), expected_error)

    def test_login_missing_fields(self):
        """
        Ensure a login attempt with a blank email field fails with a validation error.

        This test sends a POST request with an empty string for the email. It verifies
        that the response has a 400 Bad Request status code and that the response body contains
        the correct validation error for the 'email' field.
        """
        data = {
            "email": "",
            "password": "anypassword"
        }
        response = self.client.post(self.login_url, data, format='json')

        # Assert that the request was a bad request due to validation failure
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert that the response contains the specific field error
        self.assertIn('email', response.data)
        expected_error = 'This field may not be blank.'
        self.assertEqual(str(response.data['email'][0]), expected_error)
