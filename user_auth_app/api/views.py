from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken

from .serializers import RegistrationSerializer, CustomAuthTokenSerializer


class RegistrationView(APIView):
    """
    API view for user registration.
    
    Handles new user account creation with automatic token generation.
    Accepts user registration data, validates it, creates the account,
    and returns an authentication token along with user information.
    Open to all users (no authentication required).
    """
    permission_classes = [AllowAny]  # Allow unauthenticated access
    serializer_class = CustomAuthTokenSerializer

    def post(self, request):
        """
        Create a new user account and return authentication token.
        
        Processes registration data, validates user information,
        creates the account with proper password hashing, and
        generates an authentication token for immediate login.
        
        Args:
            request: HTTP request containing registration data
            
        Returns:
            Response: Success response with token and user info, or validation errors
            
        Response format (success):
            {
                "token": "authentication_token_string",
                "username": "user_username",
                "email": "user@example.com"
            }
        """
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            # Create new user account
            saved_account = serializer.save()
            
            # Generate authentication token for the new user
            token, created = Token.objects.get_or_create(user=saved_account)
            
            # Prepare response data with token and user information
            data = {
                'token': token.key,
                'username': saved_account.username,
                'email': saved_account.email
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            # Return validation errors if registration data is invalid
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(ObtainAuthToken):
    """
    Custom API view for user authentication.
    
    Handles user login using email address instead of username.
    Validates credentials, authenticates the user, and returns an
    authentication token along with user information. Extends Django's
    built-in ObtainAuthToken view with email-based authentication.
    """
    permission_classes = [AllowAny]  # Allow unauthenticated access for login
    serializer_class = CustomAuthTokenSerializer

    def post(self, request):
        """
        Authenticate user and return authentication token.
        
        Processes login credentials (email and password), validates them
        against the database, and returns an authentication token for
        successful logins. Uses email-based authentication for better UX.
        
        Args:
            request: HTTP request containing login credentials
            
        Returns:
            Response: Success response with token and user info, or authentication errors
            
        Response format (success):
            {
                "token": "authentication_token_string",
                "username": "user_username", 
                "email": "user@example.com"
            }
        """
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            # Extract authenticated user from validated data
            user = serializer.validated_data['user']
            
            # Get or create authentication token for the user
            token, created = Token.objects.get_or_create(user=user)
            
            # Prepare response data with token and user information
            data = {
                'token': token.key,
                'username': user.username,
                'email': user.email
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            # Return authentication errors if credentials are invalid
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
