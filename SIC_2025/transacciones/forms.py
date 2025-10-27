from django import forms
from .models import Transaccion, Movimiento
from datetime import date

class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = ['descripcion','fecha','monto']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class':'form-control'}),
            'fecha': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step':'0.01'}),
        }

class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ['transaccion', 'cuenta', 'monto', 'tipo']
        widgets = {
            'transaccion': forms.Select(attrs={'class':'form-select'}),
            'cuenta': forms.Select(attrs={'class':'form-select'}),
            'monto': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'tipo': forms.Select(attrs={'class':'form-select'}),
        }
