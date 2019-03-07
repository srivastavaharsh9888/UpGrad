from django.shortcuts import render

def signIn(request):
    return render(request,'login.html',{})
def signUp(request):
    return render(request,'signup.html',{})
