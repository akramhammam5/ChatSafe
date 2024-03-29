from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *
from .utils import *
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import (
    MinimumLengthValidator, CommonPasswordValidator,
    NumericPasswordValidator, UserAttributeSimilarityValidator
)
from base64 import b64encode, b64decode
from django.contrib.auth import views as auth_views
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from .forms import EditUsernameForm

import sounddevice as sd
from scipy.io.wavfile import write
from django.http import JsonResponse
from .models import AudioMessage

def record_and_send(request):
    freq = 44100
    frames = 1000000  # Record a large number of frames

    recording = sd.rec(frames, samplerate=freq, channels=2, dtype='int16')

    try:
        sd.wait()
    except KeyboardInterrupt:
        pass

    write("recording.wav", freq, recording)

    # Save the recorded audio to the database
    audio_message = AudioMessage.objects.create(audio_file="recording.wav")

    # Assuming you have a function to send audio messages
    send_audio_message(audio_message.audio_file.url)

    return JsonResponse({"message": "Audio recorded, saved, and sent successfully."})


def hide(request):
    if request.method == 'POST':
        audiofile = request.FILES.get('file')
        secretmsg = request.POST.get('text')
        outputfile = '/home/elliot/Documents/Grad/Implementation/ChatSafe/ChatSafe/audio/output.wav'
        if audiofile and secretmsg and outputfile:
            try:
                em_audio(audiofile, secretmsg , outputfile)
                return render(request,"success.html")
            except Exception as e:
                return HttpResponse(f"Error hiding message: {str(e)}")
    return render(request, 'steg.html')
        
        
def extract(request):
    if request.method == 'POST':
        audiofile = request.FILES.get('file')
        if audiofile:
            try:
                extracted_message = ex_msg(audiofile)
                return render(request, 'extracted_message.html', {'secret_message': extracted_message})
            except Exception as e:
                return render(request, 'error.html', {'error_message': f"Error extracting message: {str(e)}"})
    return render(request, 'Decode.html')
    
def index(request):
    return render(request, 'chat/index.html')

def home(request):

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('login')
        else:
            messages.success(request, 'Invalid Username or Password, Please Try Again.')
            return redirect('login')
    
    if request.user.is_authenticated:
        if Chat.objects.filter(users=request.user).exists():
            q = request.GET.get('q') if request.GET.get('q') != None else ''
            
            chats = Chat.objects.filter(users=request.user)
            if q is not "" or None:
                if User.objects.filter(username=q).exists():
                    searched_user = User.objects.get(username=q)
                    if searched_user:
                        chats = chats.filter(users=searched_user)
        else:
            chats = []
    else:
            chats = []
    context = {
        'chats': chats,
    }


    return render(request, 'chat/home.html', context)
    
def signup(request):
    if request.user.is_authenticated:
        return redirect('login')
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if User.objects.filter(username=username).exists():
            messages.success(request, "Username taken.")
        else:
            if password1 == password2:
                validate_password_manually(password1)
                user = User.objects.create_user(username=username, password=password1, email=email)
                # user.save()
                login(request, user)
                messages.success(request, f'Account Created Successfully. Welcome {username}')
                return redirect('login')
            else:
                messages.success(request, "Passwords don't match")
    return render(request, 'chat/signup.html')


@login_required(login_url='login')
def logout_user(request):
    logout(request)
    messages.success(request, "Successfully Logged Out!")
    return redirect('login')




@login_required(login_url='home')
def chat_view(request, pk):
    chat = Chat.objects.get(id=pk)
    messages = Message.objects.filter(chat=chat)

    if request.method == "POST":
        body = request.POST['body']
        Message.objects.create(user=request.user, chat=chat, body=body)

    context = {
        'body_messages': messages,
    }
    return render(request, 'chat/chat.html', context)

@login_required(login_url='home')
def new_chat(request, pk):
    if pk == 0:
        q = request.GET.get('q') if request.GET.get('q') != None else ''
        if q is not "" or None:
            if User.objects.filter(username=q).exists():
                user = User.objects.get(username=q)  
            else:
                user = None
        else:
            user = None   

    else:
        user = None 
        if Chat.objects.filter(users=request.user).exists():
            chat = Chat.objects.filter(users=request.user)
            if chat.filter(users=(User.objects.get(id=pk))).exists():
                chat = chat.get(users=(User.objects.get(id=pk)))
                return redirect('chat', pk=chat.id)
            else:
                chat = Chat.objects.create(user1=request.user, user2=User.objects.get(id=pk))
                chat.save()
                chat.users.add(request.user)
                chat.users.add(User.objects.get(id=pk))
                chat.save()
                return redirect('chat', pk=chat.id)
        else:
                chat = Chat.objects.create(user1=request.user, user2=User.objects.get(id=pk))
                chat.save()
                chat.users.add(request.user)
                chat.users.add(User.objects.get(id=pk))
                chat.save()
                return redirect('chat', pk=chat.id)


    context = {
        "user": user,
    }

    return render(request, "chat/new_chat.html", context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditUsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your username has been updated.')
            return redirect('edit_profile')
    else:
        form = EditUsernameForm(instance=request.user)
    return render(request, 'chat/edit_profile.html', {'form': form})

@login_required
def videocall(request):
    return render(request, 'chat/videocall.html', {"name": request.user.username})

def validate_password_manually(password):
    validators = [
        MinimumLengthValidator(),
        CommonPasswordValidator(),
        NumericPasswordValidator(),
        UserAttributeSimilarityValidator(),
    ]

    errors = []
    for validator in validators:
        try:
            validator.validate(password)
        except ValidationError as e:
            errors.extend(e.messages)

    if errors:
        raise ValidationError(errors)
