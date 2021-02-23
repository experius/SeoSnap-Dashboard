"""seosnap_dashboard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from rest_framework.documentation import include_docs_urls

admin.site.site_header = "SeoSnap"
admin.site.site_title = "SeoSnap Dashboard"
admin.site.index_title = "Welcome to SeoSnap Dashboard"

urlpatterns = [
    path('', admin.site.urls),
    re_path('api/(?P<version>(v1|v2))/', include('seosnap.urls')),
    url(r'^docs/', include_docs_urls(title='Api docs')),
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("favicon.ico")),
    ),
] + static('static/', document_root=settings.STATIC_ROOT)
