from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Profile


class CustomUserCreationForm(UserCreationForm):
    """Formulaire de création d'utilisateur personnalisé"""
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'role', 'phone')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CustomUserChangeForm(UserChangeForm):
    """Formulaire de modification d'utilisateur personnalisé"""
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'role', 'phone', 'address', 'bio', 'avatar')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProfileForm(forms.ModelForm):
    """Formulaire de profil utilisateur - LECTURE SEULE"""
    
    class Meta:
        model = Profile
        fields = ()  # Empty - profile fields are read-only and managed by administrators only
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields read-only if they are displayed
        for field in self.fields:
            self.fields[field].disabled = True
