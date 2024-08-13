from django.urls import path

from oauth import views as oauth_views

urlpatterns = [
    # Data Sync
    path("get-connected-data-sources/", oauth_views.ConnectedDataSourcesView.as_view(), name="get-connected-data-sources"),

    path("<str:data_source_slug>/data-sync-get-authorization-url/", oauth_views.DataSyncAuthorizationUrlView.as_view(), name="data-sync-get-authorization-url"),
    path("<str:data_source_slug>/data-sync-callback/", oauth_views.DataSyncCallbackView.as_view(), name="data-sync-app-callback"),
    path("<str:data_source_slug>/data-sync-disconnect/", oauth_views.DataSyncDisconnectView.as_view(), name="data-sync-app-disconnect"),

    path("<str:data_source_slug>/data-source-folders/", oauth_views.ConnectedDataSourcesFoldersView.as_view(), name="connected-data-source-folders"),

    path("<str:data_source_slug>/data-sync-simple-connect/", oauth_views.DataSyncSimpleAuthView.as_view(), name="data-sync-simple-app-connect"),
]
