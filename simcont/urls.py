"""
URL configuration for simcont project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from . import settings
from drf_app.views import *
from rest_framework import routers

# For Swagger
from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# More information https://proproprogs.ru/django/drf-simplerouter-i-defaultrouter
router = routers.DefaultRouter()
router.register(r'vocabulary', VocabularyViewSet)
router.register(r'lemma', LemmaViewSet)

# For Swagger
schema_view = get_schema_view(
   openapi.Info(
      title="Simcont API",
      default_version='00.00.01',
      description="REST API for application Simcont",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="gizarir@gmail.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path("__debug__/", include("debug_toolbar.urls")),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/v1/', include(router.urls)),   # http://127.0.0.1:8000/api/v1/.../ CRUD
    path('api/v1/drf-auth/', include('rest_framework.urls'))  # TODO base authentication can switch off on Prod
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
