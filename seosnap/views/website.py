from rest_framework import viewsets

from seosnap.models import Website
from seosnap.serializers import WebsiteSerializer


class WebsiteViewSet(viewsets.ModelViewSet):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer