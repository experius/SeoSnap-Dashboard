from rest_framework import serializers

from seosnap.models import Website, ExtractField, Page


class ExtractFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractField
        fields = ('website', 'name', 'css_selector', 'created_at', 'updated_at')


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ('website', 'address', 'content_type', 'status_code', 'cache_status', 'cached_at', 'created_at', 'updated_at', 'extract_fields')
        read_only_fields = ('website', 'created_at', 'updated_at')


class WebsiteSerializer(serializers.ModelSerializer):
    extract_fields = ExtractFieldSerializer(many=True, read_only=True)
    #pages = PageSerializer(many=True, read_only=True)

    class Meta:
        model = Website
        fields = ('name', 'domain', 'sitemap', 'created_at', 'updated_at', 'extract_fields')
