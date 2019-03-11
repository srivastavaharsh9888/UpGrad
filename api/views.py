from django.shortcuts import render,HttpResponse
from rest_framework import generics
from api.models import Todo
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from .serializers import TodoSerializer
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import User
from background_task import background
from django.core import validators
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.Click <a href="http://localhost:8000/login">Here</a> to login.')
    else:
        return HttpResponse('Activation link is invalid!')

@background(schedule=1)
def sendEmailVerify(user):
    try:
        mail_subject = 'Activate your account.'
        user=User.objects.get(username=user)
        message = render_to_string('acc_active_email.html', {
            'user': user,
            'uid':str(urlsafe_base64_encode(force_bytes(user.pk))),
            'token':account_activation_token.make_token(user),
        })# TEMP:
        #k=Todo.objects.create(user=user,name="Firsy Task create")
        email = EmailMessage(mail_subject, message, to=[user.email])
        email.send(fail_silently=True)
    except Exception as e:
        print(e)

@background(schedule=60)
def notify_user(user):
    user.email_user('Here is a notification', 'You have been notified')

class Register(APIView):

    def post(self, request):
        password1 = request.data.get("password1")
        password2 = request.data.get("password2")
        email=request.data.get("email")
        if password1 and password2 and password1==password2 and email:
            try:
                user_exists=User.objects.filter(username=email).exists()
                if user_exists:
                    return Response({"message":"User with this email already exists.","flag":False},status=status.HTTP_400_BAD_REQUEST)
                user = User(username=email,password=password1,email=email)
                errors = dict()
                try:
                    validate_password(password=password1, user=user)
                except Exception as e:
                    print(e)
                    errors['password'] = list(e)
                    return Response({"message":errors},status=status.HTTP_400_BAD_REQUEST)
                user=User.objects.create_user(username=email,password=password1,email=email)
                user.is_active = False
                user.save()
                sendEmailVerify(user.username)
                return Response({"message":"Activation link send to you email Verify it to continue (Do check your spam box too).","flag":True},status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({"message":"User already exists"+e,"flag":False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Password are different',"flag":False},  status=status.HTTP_400_BAD_REQUEST)

class Login(APIView):

    def post(self, request):
        name = request.data.get("email")
        password = request.data.get("password")
        try:
            user_exists=User.objects.filter(email=name)
            if not user_exists.exists():
                return Response({"message":"User with this email does not exists.","flag":False},status=status.HTTP_400_BAD_REQUEST)
            if not user_exists[0].is_active:
                return Response({"message":"Please activate your email to login.","flag":False}, status=status.HTTP_401_UNAUTHORIZED)
            if user_exists[0].check_password(password):
                user_token,created=Token.objects.get_or_create(user=user_exists[0])
                # notifications=Notification.objects.filter(shop_ids__contains=","+str(shop_obj.id)+",")
                # notification_serializer=NotificationSerializer(instance=notifications,many=True)
                return Response({"message":"User Logged in","token":user_token.key,"username":user_exists[0].username,"flag":True},status=status.HTTP_200_OK)
            else:
                return Response({"message":'Password Incorrect',"flag":False},status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(e)
            return Response({'message': 'Please enter a valid username and password.',"flag":False}, status=status.HTTP_401_UNAUTHORIZED)


class TodoApi(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes=(TokenAuthentication,)

    serializer_class=TodoSerializer
    def get_queryset(self):
        return Todo.object.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TodoOperation(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes=(TokenAuthentication,)
    serializer_class = TodoSerializer

    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user,pk=int(self.kwargs.get("pk")))
