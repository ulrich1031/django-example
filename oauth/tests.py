from django.test import TestCase, override_settings
from oauthlib.common import generate_token

from core.models import Application
from oauth.services import OAuthService


class ShopifyServiceTestCase(TestCase):
    def setUp(self):
        Application.objects.create(
            name='shopify',
            client_id='dc9ed26da8470baff3c815fa52c70199',
            client_secret='d0359d7e1e9c11d6c7379562a77ae3ec',
            authorization_url='https://{store}.myshopify.com/admin/oauth/authorize',
            token_url='https://{store}.myshopify.com/admin/oauth/access_token',
            scopes=['write_products'],
            metadata=["store"]
        )

    def test_get_authorization_url(self):
        state = generate_token()
        service = OAuthService(application_name='shopify', store='moonlight20231212', state=state)
        result = service.get_authorization_url()
        authorization_url = result[0]
        print(state)
        print(authorization_url)
        self.assertEqual(authorization_url[:5], 'https')
        self.assertEqual(result[1], state)
    
    @override_settings(OAUTHLIB_RELAX_TOKEN_SCOPE=True)
    def test_get_token(self):
        authorization_response = 'https://app.getcadenza.com/tenant-admin/connectors/applications/callback/shopify?code=40f23e60f7c4c6de00bb126f59492cb7&hmac=5bd05ac75632cecc354a8b74f7f10a1a5813e63b72522214075b4b4d8c926711&host=YWRtaW4uc2hvcGlmeS5jb20vc3RvcmUvbW9vbmxpZ2h0MjAyMzEyMTI&shop=moonlight20231212.myshopify.com&state=j5rS3UQavrD9dNOAHMevps1Chcf0Iz&timestamp=1708586349'
        state = 'j5rS3UQavrD9dNOAHMevps1Chcf0Iz'
        service = OAuthService(application_name='shopify', store='moonlight20231212', state=state)
        result = service.get_token(authorization_response)
        print(result)
        self.assertTrue('access_token' in result)


class QuickbooksServiceTestCase(TestCase):
    def setUp(self):
        Application.objects.create(
            name='quickbooks',
            client_id='AB7pxnyVzDjjPmpLbalBoG6oWtqMwIMKDhuG03FosCJyKUIcKE',
            client_secret='TBnk17MsXPV90WqPgn4TZiDXJZ9aq6AFztzkLg9R',
            authorization_url='https://appcenter.intuit.com/connect/oauth2',
            token_url='https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
            scopes=['com.intuit.quickbooks.accounting']
        )

    def test_get_authorization_url(self):
        state = generate_token()
        service = OAuthService(application_name='quickbooks', state=state)
        result = service.get_authorization_url()
        authorization_url = result[0]
        print(state)
        print(authorization_url)
        self.assertEqual(authorization_url[:5], 'https')
        self.assertEqual(result[1], state)
    
    def test_get_token(self):
        authorization_response = 'https://app.getcadenza.com/tenant-admin/connectors/applications/callback/quickbooks?code=AB11708588928yEBPRxUsyXGRxrX7nVsaZ8hVhlTfZMEDee99L&state=jKzzhkihrJSj6kQ6pzEFrVhevwAo0R&realmId=9130357994847006'
        state = 'jKzzhkihrJSj6kQ6pzEFrVhevwAo0R'
        service = OAuthService(application_name='quickbooks', state=state)
        result = service.get_token(authorization_response)
        print(result)
        self.assertTrue('access_token' in result)
    
    def test_refresh_token(self):
        state = generate_token()
        service = OAuthService(application_name='quickbooks', token={'refresh_token': 'AB11717315111x8PIoLBxQCeVc8QxQGT9s1olS7fZs6ejFp5N5'}, state=state)
        result = service.refresh_token()
        print(result)
        self.assertTrue('access_token' in result)
