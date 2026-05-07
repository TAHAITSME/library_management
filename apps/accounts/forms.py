from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import Complaint, CustomUser, Profile


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
    """Formulaire de modification du profil utilisateur."""
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'bio', 'avatar')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input'}),
            'last_name': forms.TextInput(attrs={'class': 'input'}),
            'email': forms.EmailInput(attrs={'class': 'input'}),
            'phone': forms.TextInput(attrs={'class': 'input'}),
            'address': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'bio': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'avatar': forms.FileInput(attrs={'class': 'input', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].label = 'Prenom'
        self.fields['last_name'].label = 'Nom'
        self.fields['email'].label = 'Email'
        self.fields['phone'].label = 'Telephone'
        self.fields['address'].label = 'Adresse'
        self.fields['bio'].label = 'Bio'
        self.fields['avatar'].label = 'Photo de profil'

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            return email

        queryset = CustomUser.objects.filter(email__iexact=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Cet email est deja utilise.')
        return email


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ('subject', 'category', 'priority', 'message')
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Ex: Probleme avec ma commande',
            }),
            'category': forms.Select(attrs={'class': 'select'}),
            'priority': forms.Select(attrs={'class': 'select'}),
            'message': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 6,
                'placeholder': 'Expliquez clairement le probleme rencontre...',
            }),
        }
        labels = {
            'subject': 'Sujet',
            'category': 'Categorie',
            'priority': 'Priorite',
            'message': 'Message',
        }


class ComplaintAdminForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ('status', 'priority', 'admin_response')
        widgets = {
            'status': forms.Select(attrs={'class': 'dashboard-input'}),
            'priority': forms.Select(attrs={'class': 'dashboard-input'}),
            'admin_response': forms.Textarea(attrs={
                'class': 'dashboard-input',
                'rows': 5,
                'placeholder': 'Reponse ou note interne pour cette reclamation...',
            }),
        }
        labels = {
            'status': 'Statut',
            'priority': 'Priorite',
            'admin_response': 'Reponse admin',
        }
