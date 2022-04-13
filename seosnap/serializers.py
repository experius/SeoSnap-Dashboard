from rest_framework import serializers

from seosnap.models import Website, ExtractField, Page, QueueItem


class ExtractFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractField
        fields = ('website', 'name', 'css_selector', 'created_at', 'updated_at')


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = (
            'id',
            'website', 'address',
            'content_type', 'status_code', 'cache_status', 'cached_at', 'created_at',
            'updated_at',
            'extract_fields',
            'x_magento_tags' )
        read_only_fields = ('website', 'created_at', 'updated_at')


class WebsiteSerializer(serializers.ModelSerializer):
    extract_fields = ExtractFieldSerializer(many=True, read_only=True)

    # pages = PageSerializer(many=True, read_only=True)

    class Meta:
        model = Website
        fields = (
            'name', 'domain', 'sitemap',
            'created_at', 'updated_at', 'extract_fields',
            'notification_email', 'notification_failure_rate', 'notification_cooldown'
        )


class LightPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ('address',)
        read_only_fields = ('address',)


class QueueItemSerializer(serializers.ModelSerializer):
    page = LightPageSerializer(read_only=True)

    class Meta:
        model = QueueItem
        fields = ('page', 'status')
        read_only_fields = ('page', 'priority')


class QueueSerializer(serializers.ModelSerializer):
    page = LightPageSerializer(read_only=True)

    class Meta:
        model = QueueItem
        fields = ('page_id', 'page', 'status', 'priority', 'created_at')
        read_only_fields = ('priority', 'created_at')


class WebsiteReportingSerializer(serializers.Serializer):
    errors = serializers.ListField()
