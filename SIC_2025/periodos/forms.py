from django import forms
from .models import PeriodoContable
from datetime import date

class PeriodoContableForm(forms.ModelForm):
    class Meta:
        model = PeriodoContable
        fields = ["nombre", "fecha_inicio", "fecha_fin"]
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definimos un vector de campos que queremos requerir
        campos_requeridos = ['nombre', 'fecha_inicio', 'fecha_fin']
        for campo in campos_requeridos:
            self.fields[campo].required = True
            self.fields[campo].error_messages = {'required': f'El campo {campo} es obligatorio. Porfavor, ingréselo.'}
            
    
    def clean_fecha_inicio(self):
        fecha_inicio = self.cleaned_data.get("fecha_inicio")
        if fecha_inicio and fecha_inicio < date.today():
            raise forms.ValidationError("La fecha de inicio no puede ser menor a la fecha actual.")
        return fecha_inicio
    
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                self.add_error("fecha_fin", "La fecha de fin debe ser después de la fecha de inicio.")

        return cleaned_data