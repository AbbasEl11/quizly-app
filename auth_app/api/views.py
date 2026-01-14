from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import RegistrationSerializer, CookieTokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class RegistrationView(APIView):
    """
    API view for user registration.
    
    POST: Creates a new user account with username, email, and password.
          Returns success message on successful registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Register a new user.
        
        Args:
            request: HTTP request with username, email, password, confirmed_password
            
        Returns:
            Response: Success message (201) or validation errors (400)
        """
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "User created Successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    """
    API view for user login with JWT tokens stored in HTTP-only cookies.
    
    POST: Authenticates user and returns access/refresh tokens in secure cookies.
          Also returns user information (id, username, email) in response body.
    """
    permission_classes = [AllowAny]
    serializer_class = CookieTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Authenticate user and set JWT tokens in cookies.
        
        Args:
            request: HTTP request with username and password
            
        Returns:
            Response: User data and success message with cookies set (200)
                     or authentication error (401)
        """
        res = super().post(request,*args, **kwargs)
        if res.status_code != 200:
            return res

        access_token = res.data.get("access")
        refresh_token = res.data.get("refresh")

        if access_token and refresh_token:
            res.set_cookie("access_token", access_token, httponly=True, secure=True, samesite="Lax", path="/")
            res.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite="Lax", path="/api/token/refresh/")

        user = res.data.get("user")

        res.data = {
            "detail": "Login successfully!",
            "user": user
        }

        return res


class CookieRefreshView(TokenRefreshView):
    """
    API view for refreshing JWT access token using refresh token from cookies.
    
    POST: Validates refresh token from cookie and issues new access token.
          Updates access_token cookie with new token.
    """

    def post(self, request, *args, **kwargs):
        """
        Refresh access token using refresh token from cookies.
        
        Returns:
            Response: New access token (200), 400 if cookie missing, 401 if invalid
        """
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response({"error": "Refresh token not found in cookies"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data = {'refresh': refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        access_token = serializer.validated_data.get('access')
        response = Response({"detail": "Token refreshed", "access": access_token}, status=status.HTTP_200_OK)
        
        response.set_cookie(
            key = "access_token",
            value = access_token,
            httponly = True,
            secure = True,
            samesite = 'Lax'
        )

        return response


class LogoutView(APIView):
    """
    API view for user logout with token blacklisting.
    
    POST: Blacklists the refresh token and deletes both access and refresh cookies.
          Requires authentication via access token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Logout user by blacklisting refresh token and clearing cookies.
        
        Returns:
            Response: Success message (200) or error if token invalid (400)
        """
        refresh_token = request.COOKIES.get('refresh_token')
        
        try:
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            res = Response({"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."}, status=status.HTTP_200_OK)
            res.delete_cookie('access_token', path='/')
            res.delete_cookie('refresh_token', path='/api/token/refresh/')
            
            return res
        except Exception as e:  
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)
        

