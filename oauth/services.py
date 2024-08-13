from django.conf import settings
from oauth.clients import CoreOAuthClient
from core.models import DataSource


class Adapter:
    def __init__(self, application_obj, metadata=None, oauth_info=None, route_slug='applications', **kwargs):
        self.application_obj = application_obj
        self.oauth_info = oauth_info
        if oauth_info:
            self.client_id = oauth_info['client_id']
            self.client_secret = oauth_info['client_secret']
            self.scopes = oauth_info['scopes']
        else:
            self.client_id = application_obj.client_id
            self.client_secret = application_obj.client_secret
            self.scopes = application_obj.scopes
        self.redirect_uri = settings.OAUTH_REDIRECT_URI.format(route_slug=route_slug, application_slug=application_obj.slug)

        self.state = kwargs.get('state', None)
        self.metadata = metadata or {}
        self.token = None
        if kwargs.get('token'):
            self.token = kwargs.get('token')

    def customize_authorization_url(self):
        if self.oauth_info:
            return self.oauth_info['authorization_url'].format(**self.metadata)
        return self.application_obj.authorization_url.format(**self.metadata)

    def customize_token_url(self):
        if self.oauth_info:
            return self.oauth_info['token_url'].format(**self.metadata)
        return self.application_obj.token_url.format(**self.metadata)

    def get_params(self):
        _kwargs = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope': self.scopes,
        }
        extra_kwargs = {
            'authorize_base_url': self.customize_authorization_url(),
            'client_secret': self.client_secret,
            'token_url': self.customize_token_url(),
        }
        if self.token:
            _kwargs['token'] = self.token
        return _kwargs, extra_kwargs


class OAuthService:
    def __init__(self, application_slug, is_data_source=False, *args, **kwargs):
        self.application_slug = application_slug
        self.is_data_source = is_data_source
        api_adapter = self.load_api_adapter(*args, **kwargs)
        _kwargs, extra_kwargs = api_adapter.get_params()
        self.core_oauth_client = CoreOAuthClient(_kwargs, extra_kwargs)

    def load_api_adapter(self, *args, **kwargs):
        if self.is_data_source:
            application_obj = DataSource.objects.get(slug=self.application_slug)
        metadata = {}
        for item in application_obj.metadata or []:
            name = item['name']
            metadata[name] = kwargs[name]
        route_slug = 'applications'
        if self.is_data_source:
            route_slug = 'data-sources'
        return Adapter(application_obj, metadata=metadata, route_slug=route_slug, *args, **kwargs)

    def get_authorization_url(self):
        return self.core_oauth_client.get_authorization_url()

    def get_token(self, authorization_response):
        self.core_oauth_client.client.scope = None
        return self.core_oauth_client.fetch_token(authorization_response)

    def refresh_token(self):
        self.core_oauth_client.client.scope = None  # some connectors such as `Microsoft Identity Platform`, scopes changed
        return self.core_oauth_client.refresh_token()
