from rest_framework import serializers
from core import models


class DataSourceSerializer(serializers.ModelSerializer):
    """show data source (connected data source page)"""
    is_connected = serializers.SerializerMethodField()
    folders = serializers.SerializerMethodField()

    class Meta:
        model = models.DataSource
        fields = ['uuid', 'name', 'slug', 'auth_method', 'logo', 'description', 'is_connected', 'is_own_app', 'metadata', 'folders']

    def get_is_connected(self, obj):
        """return True if the tenant connected the application"""
        return getattr(obj, 'is_connected') or False
    
    def get_folders(self, obj):
        """CZ-114, show user selected folders"""
        folders = getattr(obj, 'folders')
        if getattr(obj, 'slug') == 'sharepoint':
            return folders or {}
        else:
            return folders or []


class DataConnectionSerializer(serializers.ModelSerializer):
    data_source = serializers.SerializerMethodField()

    class Meta:
        model = models.DataConnection
        fields = ['uuid', 'data_source']

    def get_data_source(self, obj):
        try:
            data_source_obj = models.DataSource.objects.get(slug__icontains=obj.data_source)
            return DataSourceSerializer(data_source_obj).data
        except models.DataSource.DoesNotExist:
            return None
