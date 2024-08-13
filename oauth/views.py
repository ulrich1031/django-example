import os
import logging
import json
from datetime import datetime, timedelta

from django.utils import timezone
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from oauthlib.common import generate_token

from oauth.utils.google_drive import get_google_drive_folders
from oauth.utils.sharepoint import get_sharepoint_sites, get_sharepoint_folders
from core.models import DataSource, DataConnection
from core.services import DataConnectionService
from oauth import serializers as oauth_serializers
from rest_framework.permissions import IsAuthenticated
from authentication.permissions import TenantAdminPermission
from oauth.services import OAuthService

logger = logging.getLogger(__name__)


class ConnectedDataSourcesView(generics.ListAPIView):
    """user can retrieve all data sources, admin or common user"""
    serializer_class = oauth_serializers.DataSourceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        show_all = self.request.GET.get('show_all') == 'yes'
        user = self.request.user
        connected_apps = DataConnection.objects.filter(tenant=user.tenant).values_list("data_source", flat=True)
        if show_all:
            data_sources = DataSource.objects.all()
        else:
            data_sources = user.tenant.allowed_data_sources.all()
        for app in data_sources:
            if app.slug in connected_apps:
                app.is_connected = True
                data_connection = DataConnection.objects.get(tenant=user.tenant, data_source=app.slug)
                other_info = data_connection.other_info or {}
                folders = other_info.get('folders') # CZ-114, show user selected folders
                if app.slug == 'sharepoint':
                    app.folders = folders or {}
                else:
                    app.folders = folders or []
            else:
                app.is_connected = False
                app.folders = None
        return data_sources


class DataSyncAuthorizationUrlView(APIView):
    """OAuth data sync"""
    permission_classes = [IsAuthenticated, TenantAdminPermission]

    def post(self, request, format=None, *args, **kwargs):
        data_source_slug = kwargs['data_source_slug']
        data_source_instance = DataSource.objects.get(slug=data_source_slug)
        _kwargs = {}
        metadata = data_source_instance.metadata or []
        for item in metadata:
            name = item['name']
            _kwargs[name] = request.data.get(name)
            cache.set(f'{data_source_slug}_{name}_of_user_{request.user.id}', request.data.get(name))
        
        oauth_info = None
        if not data_source_instance.is_own_app:
            client_id = request.data.get('client_id')
            client_secret = request.data.get('client_secret')
            scopes = request.data.get('scopes')
            authorization_url = request.data.get('authorization_url')
            token_url = request.data.get('token_url')
            oauth_info = {
                'client_id': client_id,
                'client_secret': client_secret,
                'scopes': json.loads(scopes),
                'authorization_url': authorization_url,
                'token_url': token_url
            }
            cache.set(f'{data_source_slug}_oauth_data_of_user_{request.user.id}', oauth_info)

        state = generate_token()
        service = OAuthService(
            application_slug=data_source_slug,
            is_data_source=True,
            state=state,
            oauth_info=oauth_info,
            **_kwargs
        )
        result = service.get_authorization_url()
        authorization_url = result[0]
        cache.set(f'{data_source_slug}_state_of_user_{request.user.id}', state)
        
        response = Response(authorization_url, status=status.HTTP_200_OK)
        return response


class DataSyncCallbackView(APIView):
    """OAuth app"""
    permission_classes = [IsAuthenticated, TenantAdminPermission]

    def post(self, request, format=None, *args, **kwargs):
        if 'WEBSITE_HOSTNAME' not in os.environ:
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # localhost transport is http

        data_source_slug = kwargs['data_source_slug']
        data_source_instance = DataSource.objects.get(slug=data_source_slug)

        _kwargs = {}
        metadata = data_source_instance.metadata or []
        for item in metadata:
            name = item['name']
            _kwargs[name] = cache.get(f'{data_source_slug}_{name}_of_user_{request.user.id}')

        state = cache.get(f'{data_source_slug}_state_of_user_{request.user.id}')
        callback_url = request.data['callback_url']

        oauth_info = None
        if not data_source_instance.is_own_app:
            oauth_info = cache.get(f'{data_source_slug}_oauth_data_of_user_{request.user.id}')

        service = OAuthService(application_slug=data_source_slug, is_data_source=True, state=state, oauth_info=oauth_info, **_kwargs)
        result = service.get_token(callback_url)
        logger.info(f"OAuth token result: {result}")

        defaults = {
            "auth_info": {"access_token": result['access_token']},
            "other_info": _kwargs
        }

        if 'expires_at' in result:
            defaults['access_token_expires_at'] = timezone.make_aware(datetime.fromtimestamp(result['expires_at']))

        if 'refresh_token' in result:
            defaults['refresh_token'] = result['refresh_token']

        if 'x_refresh_token_expires_in' in result:
            refresh_token_expires_in = result['x_refresh_token_expires_in']
            defaults['refresh_token_expires_at'] = timezone.now() + timedelta(seconds=refresh_token_expires_in)

        if not data_source_instance.is_own_app:
            defaults['client_id'] = oauth_info['client_id']
            defaults['client_secret'] = oauth_info['client_secret']
            defaults['scopes'] = oauth_info['scopes']
            defaults['authorization_url'] = oauth_info['authorization_url']
            defaults['token_url'] = oauth_info['token_url']

        DataConnection.objects.update_or_create(
            tenant=request.user.tenant,
            data_source=data_source_slug,
            defaults=defaults
        )

        return Response('ok', status=status.HTTP_200_OK)


class DataSyncDisconnectView(APIView):
    """OAuth app"""
    permission_classes = [IsAuthenticated, TenantAdminPermission]

    def post(self, request, *args, **kwargs):
        user = request.user
        data_connection = DataConnection.objects.filter(tenant=user.tenant, data_source=kwargs['data_source_slug']).first()
        # NOTE: it's important to call indivdual instance's delete method!!! in order to overwrite delete()
        if data_connection:
            data_connection.delete()
        return Response('ok', status=status.HTTP_200_OK)


class ConnectedDataSourcesFoldersView(APIView):
    """CZ-114, 
     - retrieve folders from GoogleDrive, Sharepoint, etc.
     - save user selected folders
    """
    permission_classes = [IsAuthenticated, TenantAdminPermission]

    def get(self, request, *args, **kwargs):
        """return folders (or sites) as options on FE"""
        user = request.user
        tenant = user.tenant
        data_source_slug = kwargs['data_source_slug']
        data_connection = DataConnection.objects.filter(tenant=tenant, data_source=data_source_slug).first()
        if data_connection:
            access_token = data_connection.auth_info.get('access_token')
            if data_source_slug == 'googledrive':
                status_code, result = get_google_drive_folders(access_token)
                if status_code == 401:
                    service = DataConnectionService(data_connection=data_connection)
                    service.refresh_token()
                    data_connection = DataConnection.objects.filter(tenant=tenant, data_source=data_source_slug).first()
                    access_token = data_connection.auth_info.get('access_token')
                    status_code, result = get_google_drive_folders(access_token)
                logger.info(f"fetch Google Drive result:{status_code} {result}")
                folders = result.get('files')

                if folders and data_connection.other_info.get('folders'):
                    self.update_google_drive_name_of_folders(data_connection, folders)
                return Response(folders)
            
            elif data_source_slug == 'facebook':
                pages = [
                    {"id": "Reviews", "name": "Reviews"},
                    {"id": "Posts", "name": "Posts"},
                    {"id": "Comments", "name": "Comments"},
                ]
                return Response(pages)
            
            elif data_source_slug == 'sharepoint':
                result = None
                site_id = self.request.GET.get('site_id')
                is_search_sites = self.request.GET.get('is_search_sites') == 'yes'
                if is_search_sites:
                    status_code, result = get_sharepoint_sites(access_token)
                else:
                    status_code, result = get_sharepoint_folders(site_id, access_token)
                if status_code == 401:
                    service = DataConnectionService(data_connection=data_connection)
                    service.refresh_token()
                    data_connection = DataConnection.objects.filter(tenant=tenant, data_source=data_source_slug).first()
                    access_token = data_connection.auth_info.get('access_token')
                    if is_search_sites:
                        status_code, result = get_sharepoint_sites(access_token)
                    else:
                        status_code, result = get_sharepoint_folders(site_id, access_token)
                logger.info(f"fetch Sharepoint result:{status_code} {result}")

                if not is_search_sites and site_id and status_code == 200 and data_connection.other_info.get('folders'):
                    self.update_sharepoint_name_of_folders(data_connection, site_id, result)
                return Response(result)

        return Response([])
    
    def post(self, request, format=None, *args, **kwargs):
        user = request.user
        tenant = user.tenant
        data_source_slug = kwargs['data_source_slug']
        data_connection = DataConnection.objects.filter(tenant=tenant, data_source=data_source_slug).first()
        if data_connection:
            other_info = data_connection.other_info or {}
            new_data = dict(request.data)
            other_info.update(new_data)
            data_connection.other_info = other_info
            data_connection.save()
        return Response('OK')
    
    @staticmethod
    def update_google_drive_name_of_folders(data_connection, folders):
        """CZ-114, folder name might be changed after selected
        sample folders: [{'id': '1ZdGKKqT6iZFyvxYeJhAVo2xhfbgvNTHg', 'name': 'helle2024'}]
        sample `data_connection.other_info.get('folders')`: [{'id': '1ZdGKKqT6iZFyvxYeJhAVo2xhfbgvNTHg', 'name': 'helle2030'}]
        """
        new_folder_info = {item['id']: item['name'] for item in folders}
        current_folders = data_connection.other_info.get('folders')
        for item in current_folders:
            if item['id'] in new_folder_info:
                item['name'] = new_folder_info[item['id']]
        data_connection.save()

    @staticmethod
    def update_sharepoint_name_of_folders(data_connection, site_id, result):
        """CZ-114, folder name might be changed after selected
        
        sample `result`: [{'id': '01UPPU7NA', 'name': '16'}, {'id': '0NUKOZL', 'name': '17'}]
        sample `data_connection.other_info.get('folders')`: {'shenan701,ab1f3419': [{'id': '01JIQJSN2', 'name': 'folder2024'}]}
        """
        new_folder_info = {item['id']: item['name'] for item in result}

        root = data_connection.other_info.get('folders')
        if site_id in root:
            folders_of_site = root.get(site_id)
            for item in folders_of_site:
                if item['id'] in new_folder_info:
                    item['name'] = new_folder_info[item['id']]
            data_connection.save()


class DataSyncSimpleAuthView(APIView):
    """API Key or Basic Auth app"""
    permission_classes = [IsAuthenticated, TenantAdminPermission]

    def post(self, request, format=None, *args, **kwargs):
        data_source_slug = kwargs['data_source_slug']
        data = dict(request.data)
        
        auth_info = {}
        username = data.pop('username', None)
        if username:
            auth_info['username'] = username
        password = data.pop('password', None)
        if password:
            auth_info['password'] = password
        api_key = data.pop('api_key', None)
        if api_key:
            auth_info['api_key'] = api_key
        
        other_info = json.dumps(data)
        
        defaults = {
            "auth_info": auth_info,
            "other_info": json.loads(other_info)
        }

        DataConnection.objects.update_or_create(
            tenant=request.user.tenant,
            data_source=data_source_slug,
            defaults=defaults
        )
        
        response = Response('OK', status=status.HTTP_200_OK)
        return response
