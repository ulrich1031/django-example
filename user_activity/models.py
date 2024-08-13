from django.conf import settings  
from django.db import models  
from django.utils import timezone  

class Visit(models.Model):  
    user = models.ForeignKey(  
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True  
    )  
    session_key = models.CharField(max_length=40)  
    path = models.CharField(max_length=255)  
    timestamp = models.DateTimeField(default=timezone.now)  

    def __str__(self):  
        return f"{self.user} visited {self.path} at {self.timestamp}"