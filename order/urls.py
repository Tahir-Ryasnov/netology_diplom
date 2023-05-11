"""order URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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


from allauth.account.views import PasswordResetView, ConfirmEmailView
from django.contrib import admin
from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework.schemas import get_schema_view

from backend.views import HomeView


TITLE = 'API Service'
DESCRIPTION = 'Service for ordering goods for retail chains'

schema_view = get_schema_view(title=TITLE)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('api/v1/', include('backend.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/password/reset/', PasswordResetView.as_view(), name='account-reset-password'),
    path('accounts/confirm-email/', ConfirmEmailView.as_view(), name='account-email-verification_sent'),
    path('docs/', include_docs_urls(title=TITLE, description=DESCRIPTION)),
    path('schema/', schema_view),
]
