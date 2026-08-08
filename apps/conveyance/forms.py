from django import forms
from .models import Conveyance, ConveyanceItem
from django.forms import inlineformset_factory

class ConveyanceForm(forms.ModelForm):
    class Meta:
        model = Conveyance
        fields = ['student', 'date', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class ConveyanceItemForm(forms.ModelForm):
    class Meta:
        model = ConveyanceItem
        fields = ['client', 'assignment', 'from_location', 'to_location', 'transport', 'amount', 'description', 'attachment']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

ConveyanceItemFormSet = inlineformset_factory(
    Conveyance, ConveyanceItem, form=ConveyanceItemForm,
    extra=1, can_delete=True
)
