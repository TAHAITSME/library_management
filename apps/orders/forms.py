from django import forms
from .models import Order, OrderItem


class OrderForm(forms.ModelForm):
    """Formulaire de commande"""
    
    class Meta:
        model = Order
        fields = ['shipping_address', 'notes']
        widgets = {
            'shipping_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Adresse de livraison complète'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes supplémentaires (optionnel)'
            }),
        }
