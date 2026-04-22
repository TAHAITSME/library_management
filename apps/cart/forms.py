from django import forms
from . models import CartItem


class AddToCartForm(forms.ModelForm):
    """Formulaire pour ajouter au panier"""
    
    class Meta:
        model = CartItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1,
                'style': 'width: 80px;'
            }),
        }
