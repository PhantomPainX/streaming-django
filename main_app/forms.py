import email
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.forms.widgets import PasswordInput, TextInput, EmailInput

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(widget=EmailInput(attrs={'placeholder': 'Email de la cuenta'}))

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(widget=PasswordInput(attrs={'placeholder': 'Nueva contraseña'}))
    new_password2 = forms.CharField(widget=PasswordInput(attrs={'placeholder': 'Repetir nueva contraseña'}))

    error_messages = {
        'password_mismatch': 'Las contraseñas no coinciden'        
    }

    def clean_new_password2(self):
        new_password2 = self.cleaned_data['new_password2']
        new_password1 = self.cleaned_data['new_password1']
        if new_password1 != new_password2:
            raise forms.ValidationError(self.error_messages['password_mismatch'],code='password_mismatch',)
        else:
            return new_password2

# class CustomAuthForm(forms.Form):
#     username_email = forms.CharField(widget=TextInput(attrs={'placeholder': 'Usuario o Email'}))
#     password = forms.CharField(widget=PasswordInput(attrs={'placeholder':'Contraseña'}))

class RegistroForm(UserCreationForm):
    username = forms.CharField(widget=TextInput(attrs={'placeholder': 'Nombre de Usuario'}))
    email = forms.EmailField(widget=EmailInput(attrs={'placeholder': 'Email'}))
    password1 = forms.CharField(widget=PasswordInput(attrs={'placeholder':'Contraseña'}))
    password2 = forms.CharField(widget=PasswordInput(attrs={'placeholder':'Confirmar Contraseña'}))

    error_messages = {
        'duplicate_username': 'El nombre de usuario ya existe',
        'duplicate_email': 'El email ya existe',
        'password_mismatch': 'Las contraseñas no coinciden',
        'cataracter_invalido': "El caracter '@' esta reservado para emails",
    }

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data['username']
        user_exists = User.objects.filter(username=username).exists()
        if "@" in username:
            raise forms.ValidationError(self.error_messages['cataracter_invalido'],code='cataracter_invalido',)
        elif user_exists:
            raise forms.ValidationError(self.error_messages['duplicate_username'],code='duplicate_username',)
        else:
            return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        email_exists = User.objects.filter(email=email).exists()
        if email_exists:
            raise forms.ValidationError(self.error_messages['duplicate_email'],code='duplicate_email',)
        else:
            return email

    def clean_password2(self):
        password2 = self.cleaned_data['password2']
        password1 = self.cleaned_data['password1']
        if password1 != password2:
            raise forms.ValidationError(self.error_messages['password_mismatch'],code='password_mismatch',)
        else:
            return password2


class ContactoForm(forms.Form):
    nombre_completo = forms.CharField(widget=TextInput(attrs={'placeholder': 'Nombre y Apellidos'}))
    email = forms.EmailField(widget=EmailInput(attrs={'placeholder': 'Tu email'}))
    asunto = forms.CharField(widget=TextInput(attrs={'placeholder': 'Asunto'}))
    mensaje = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Mensaje'}))