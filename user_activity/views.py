# user_activity/views.py  
from django.shortcuts import render  
from django.utils import timezone  
from datetime import timedelta  
from .models import Visit  
from django.db.models import Count  

def user_activity_overview(request):  
    total_visits = Visit.objects.count()  
    last_week = timezone.now() - timedelta(days=7)  
    recent_visits = Visit.objects.filter(timestamp__gte=last_week)  
    path_visits = Visit.objects.filter(path='/admin/').count()  
    visits_per_user = Visit.objects.values('user__username').annotate(visits=Count('id')).order_by('-visits')  

    context = {  
        'total_visits': total_visits,  
        'recent_visits': recent_visits,  
        'path_visits': path_visits,  
        'visits_per_user': visits_per_user,  
    }  
    return render(request, 'user_activity/overview.html', context)