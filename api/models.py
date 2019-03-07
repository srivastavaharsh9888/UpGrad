from django.db import models
from django.contrib.auth.models import User

class Todo(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    description=models.TextField(blank=True,null=True)
    reminder=models.DateTimeField(auto_now_add=True)
    created_at=models.DateTimeField(auto_now_add=True)
    completed=models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'name')
