from django.urls import path
from auth_app.api.views import RegistrationView, LoginView, LogoutView, CookieRefreshView

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieRefreshView.as_view(), name='refresh_token'),
]
