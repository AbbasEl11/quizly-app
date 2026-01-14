"""
URL configuration for Authentication API endpoints.

Provides routes for:
- User registration
- Login with JWT tokens in HTTP-only cookies
- Logout with token blacklisting
- Token refresh using refresh token from cookies
"""
from django.urls import path
from auth_app.api.views import RegistrationView, LoginView, LogoutView, CookieRefreshView

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieRefreshView.as_view(), name='refresh_token'),
]
