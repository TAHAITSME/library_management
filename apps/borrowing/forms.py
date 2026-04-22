from django import forms
from .models import Borrow, BorrowRequest


class BorrowRequestForm(forms.ModelForm):
    """Formulaire de demande d'emprunt"""
    
    class Meta:
        model = BorrowRequest
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notes supplémentaires (optionnel)'
            }),
        }


class BorrowForm(forms.ModelForm):
    """Formulaire d'emprunt"""
    
    class Meta:
        model = Borrow
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notes supplémentaires (optionnel)'
            }),
        }
