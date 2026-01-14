from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles user creation with password confirmation and email uniqueness validation.
    Passwords are hashed before saving to database.
    """
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'required': True
            }
        }

    def validate_confirmed_password(self, value):
        """
        Validate that password and confirmed_password match.
        
        Args:
            value: Confirmed password value
            
        Returns:
            str: Validated password
            
        Raises:
            ValidationError: If passwords don't match
        """
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def validate_email(self, value):
        """
        Validate that email is unique.
        
        Args:
            value: Email address
            
        Returns:
            str: Validated email
            
        Raises:
            ValidationError: If email already exists
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self):
        """
        Create and save new user with hashed password.
        
        Returns:
            User: Newly created user instance
        """
        pw = self.validated_data['password']

        account = User(email=self.validated_data['email'], username=self.validated_data['username'])
        account.set_password(pw)
        account.save()
        return account


class CookieTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes user information in token response.
    
    Extends TokenObtainPairSerializer to add user data (id, username, email)
    to the response payload for client-side use.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

    def validate(self, attrs):
        """
        Validate credentials and add user data to response.
        
        Args:
            attrs: Authentication credentials
            
        Returns:
            dict: Token data with added user information
        """
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email
        }
        return data
    
    
