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

# More information https://proproprogs.ru/django/drf-simplerouter-i-defaultrouter
router = routers.DefaultRouter()
router.register(r'vocabulary', VocabularyViewSet)
router.register(r'lemma', LemmaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path("__debug__/", include("debug_toolbar.urls")),
    path('api/v1/', include(router.urls)),   # http://127.0.0.1:8000/api/v1/.../ CRUD
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
