from base64 import urlsafe_b64encode
from email import message
from http.client import HTTPResponse
from lib2to3.pgen2.tokenize import generate_tokens
from tarfile import LENGTH_NAME
from urllib.request import HTTPRedirectHandler
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from gfg import settings
from django.core.mail import send_mail,EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes,force_str
from . tokens import generate_tokens

# Create your views here.
def home(request):
    return render(request,'authentication/index.html')

def signup(request):
    if request.method=="POST":
        username=request.POST.get('username')
        fname=request.POST['fname']
        lname=request.POST['lname']
        email=request.POST['email']
        pass1=request.POST['pass1']
        pass2=request.POST['pass2']
        
        if User.objects.filter(username=username):
            messages.error(request,"Username already exists please try other username")
            return redirect('home')
        if User.objects.filter(email=email):
            messages.error(request,'Email already registered')
            return redirect('home')
        if len(username)>10:
            messages.error(request,'Username must be under 10 characters')
        if pass1!=pass2:
            messages.error(request,"Passwords didn't  match")
        if not username.isalnum():
            messages.error(request,'Username must be alpha-numeric')
            return redirect('home')
            
        myuser=User.objects.create_user(username,email,pass1)
        myuser.first_name=fname
        myuser.last_name=lname
        myuser.is_active=False
        myuser.save()
        messages.success(request,"Your account has been successfully created.we have sent you a confirmational mail,please confrim your mail in order to activate your account")
        #WELCOME EMAIL
        subject="Welcome to site-login!"
        message="Hello"+myuser.first_name+"!!\n"+'Welcome to my site!!\n Thank you for visiting our website \n we have also sent you a confirmational email,please confirm your email address in order to activate your account. \n\n Thanking You\n Shiva Sai'
        from_email=settings.EMAIL_HOST_USER
        to_list=[myuser.email]
        send_mail(subject,message,from_email,to_list,fail_silently=True)
        
        #Email address confirmational mail
        current_site=get_current_site(request)
        email_subject='Confirm your mail @ mysite - Django login!!'
        message2=render_to_string('email_confirmation.html',{
            'name':myuser.first_name,
            'domain':current_site.domain,
            'uid':urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token':generate_tokens.make_token(myuser)
        })
        email=EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently=True
        email.send()
    
        return redirect('signin')
    return render(request,'authentication/signup.html')

def signin(request):
    if request.method=='POST':
        username=request.POST['username']
        pass1=request.POST['pass1']
        user=authenticate(username=username,password=pass1)
        if user is not None:
            login(request,user)
            fname=user.first_name
            return render(request,'authentication/index.html',{'fname':fname})
        else:
            messages.error(request,"Bad Credentials")
            return redirect('home')
    return render(request,'authentication/signin.html')

def signout(request):
    logout(request)
    messages.success(request,"Logged out successfully")
    
    return redirect('home')

def activate(request,uidb64,token):
    try:
        uid=force_str(urlsafe_base64_decode(uidb64))
        myuser=User.objects.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser=None
    
    if myuser is not None and generate_tokens.check_token(myuser,token):
        myuser.is_active=True
        myuser.save()
        login(request,myuser)
        return redirect('home')
    else:
        return render(request,'activation_failed.html')