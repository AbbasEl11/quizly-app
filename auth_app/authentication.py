from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class that reads access token from HTTP-only cookies.
    
    Extends JWTAuthentication to extract JWT token from 'access_token' cookie
    instead of Authorization header, providing better XSS protection.
    """
    
    def authenticate(self, request):
        """
        Authenticate user using JWT token from cookies.
        
        Args:
            request: HTTP request with access_token cookie
            
        Returns:
            tuple: (user, validated_token) if authentication successful, None otherwise
        """
        access_token = request.COOKIES.get('access_token')
        if access_token is None:
            return None
        validated_token = self.get_validated_token(access_token)
        return self.get_user(validated_token), validated_token