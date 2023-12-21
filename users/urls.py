from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import EmailTokenObtainPairView, RegisterView

# TODO need add change_password route https://chat.openai.com/share/1f4ed8bc-25c1-4060-accc-a31beaf22ef9
urlpatterns = [
    path('register/', RegisterView.as_view(), name='user_register'),
    path('token/obtain/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
