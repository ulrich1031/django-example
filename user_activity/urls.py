# user_activity/urls.py  
from django.urls import path  
from . import views  

urlpatterns = [  
    path('overview/', views.user_activity_overview, name='user_activity_overview'),  
]