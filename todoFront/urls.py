from django.conf.urls import url
from . import views

urlpatterns = [
    url('signUp/$',views.signUp,name='todo-signUp'),
    url('signIn/$',views.signIn,name='todo-signIn'),
]
