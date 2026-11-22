from django import forms

from .models import Idea


class IdeaForm(forms.ModelForm):
    class Meta:
        model = Idea
        fields = ['type', 'title', 'content']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6,
                                             'placeholder': 'Décrivez votre idée...'}),
        }
        labels = {
            'type': 'Type',
            'title': 'Titre',
            'content': 'Contenu',
        }