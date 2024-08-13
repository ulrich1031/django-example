from django.utils.deprecation import MiddlewareMixin  
from .models import Visit  

class UserVisitsMiddleware(MiddlewareMixin):  
    def process_request(self, request):  
        session_key = request.session.session_key  
        if not session_key:  
            request.session.create()  
            session_key = request.session.session_key  

        if request.user.is_authenticated:  
            Visit.objects.create(  
                user=request.user,  
                session_key=session_key,  
                path=request.path  
            )  
        else:  
            Visit.objects.create(  
                session_key=session_key,  
                path=request.path  
            )