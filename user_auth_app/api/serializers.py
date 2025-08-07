from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles user account creation with password confirmation and email validation.
    Ensures passwords match and email addresses are unique before creating new users.
    Automatically hashes passwords for secure storage.
    """
    # Additional field for password confirmation (not stored in database)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password']
        extra_kwargs = {
            'password': {
                'write_only': True  # Password should never be returned in responses
            }
        }

    def save(self):
        """
        Create and save a new user account with validation.
        
        Validates that passwords match and email is unique before creating
        the user account. Properly hashes the password for secure storage.
        
        Returns:
            User: The newly created user instance
            
        Raises:
            ValidationError: If passwords don't match or email already exists
        """
        pw = self.validated_data['password']
        repeated_pw = self.validated_data['repeated_password']
        email = self.validated_data['email']

        # Validate that passwords match
        if pw != repeated_pw:
            raise serializers.ValidationError({'error': 'Passwords don\'t match'})

        # Check if email is already in use
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'error': 'This email address already exists.'})

        # Create new user account with provided data
        account = User(email=self.validated_data['email'],
                       username=self.validated_data['username'])
        account.set_password(pw)  # Properly hash the password
        account.save()
        return account


class CustomAuthTokenSerializer(serializers.Serializer):
    """
    Custom serializer for email-based authentication.
    
    Handles user login using email address instead of username.
    Validates credentials and returns the authenticated user object
    for token generation. Provides secure authentication with proper
    error handling for invalid credentials.
    """
    # Email field for user identification
    email = serializers.EmailField()
    # Password field with secure input styling
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False  # Preserve password whitespace
    )

    def validate(self, attrs):
        """
        Validate user credentials and authenticate the user.
        
        Performs email-based authentication by first finding the user
        by email, then authenticating with their username and password.
        
        Args:
            attrs (dict): Dictionary containing email and password
            
        Returns:
            dict: Validated attributes including the authenticated user
            
        Raises:
            ValidationError: If credentials are invalid or missing
        """
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                # Find user by email address
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid email or password.")

            # Authenticate using username (Django's default auth backend)
            user = authenticate(username=user_obj.username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            raise serializers.ValidationError("Both email and password are required.")

        # Add authenticated user to validated data
        attrs['user'] = user
        return attrs
