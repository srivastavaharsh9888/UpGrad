from .models import Todo
from rest_framework import serializers

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        models=Todo
        fields='__all__'
        extra_kwargs = {'user': {'required': False}}
