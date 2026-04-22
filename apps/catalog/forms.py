from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    """Formulaire d'avis sur un livre"""
    
    rating = forms.ChoiceField(
        choices=[(i, f'{i} étoile{"s" if i > 1 else ""}') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True,
        label='Note'
    )
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Votre avis sur ce livre...'
            }),
        }
    
    def clean_rating(self):
        """Ensure rating is converted to integer"""
        rating = self.cleaned_data.get('rating')
        if rating:
            try:
                return int(rating)
            except (ValueError, TypeError):
                raise forms.ValidationError('Note invalide')
        raise forms.ValidationError('Veuillez sélectionner une note')


class SearchForm(forms.Form):
    """Formulaire de recherche de livres"""
    
    query = forms.CharField(
        label='Rechercher',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Titre, auteur, ISBN...'
        })
    )
    category = forms.CharField(
        label='Catégorie',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrer par catégorie'
        })
    )
