from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import CustomUser, Profile


class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Nom d\'utilisateur, email ou mot de passe incorrect. Vérifiez vos informations et réessayez.',
        'inactive': 'Ce compte est désactivé. Contactez l\'administrateur si nécessaire.',
    }

    username = forms.CharField(
        label='Nom d\'utilisateur ou email',
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'})
    )

    def clean(self):
        username = self.cleaned_data.get('username')

        if username and '@' in username:
            UserModel = get_user_model()
            try:
                user = UserModel.objects.get(email__iexact=username)
            except UserModel.DoesNotExist:
                user = None
            else:
                self.cleaned_data['username'] = user.get_username()

        return super().clean()


class CustomUserCreationForm(UserCreationForm):
    """Formulaire de création d'utilisateur personnalisé"""
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
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
