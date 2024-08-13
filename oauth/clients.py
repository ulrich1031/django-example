from requests_oauthlib import OAuth2Session


class CoreOAuthClient:
    def __init__(self, _kwargs, extra_kwargs):
        """
        :param client_id: client_id, app_id or app_key from Applications
        :param redirect_uri: e.g., https://app.getcadenza.com/callback/
        :param client_secret: client_secret or app_secret from Applications
        :param authorize_base_url: e.g., https://quickstart-68621f43.myshopify.com/admin/oauth/authorize
        :param token_url: e.g., https://quickstart-68621f43.myshopify.com/admin/oauth/access_token
        :param state: we can provide state with oauthlib.common.generate_token()
        :param token: for refresh access token, e.g. `{'refresh_token': refresh_token}`
        """
        self.client_id = _kwargs['client_id']
        self.client_secret = extra_kwargs.get('client_secret', None)
        self.authorize_base_url = extra_kwargs.get('authorize_base_url', None)
        self.token_url = extra_kwargs.get('token_url', None)

        self.client = OAuth2Session(**_kwargs)

    def get_authorization_url(self):
        return self.client.authorization_url(self.authorize_base_url)

    def fetch_token(self, authorization_response):
        """
        :param authorization_response: whole url redirect from the Application,
            e.g. `https://app.getcadenza.com/?code=cc&hmac=dd&host=ff&
                    shop=quickstart-68621f43.myshopify.com&state=ss&timestamp=1701935599`
        """
        return self.client.fetch_token(self.token_url,
                                       authorization_response=authorization_response,
                                       client_secret=self.client_secret)

    def refresh_token(self):
        return self.client.refresh_token(self.token_url,
                                         client_id=self.client_id,
                                         client_secret=self.client_secret)
