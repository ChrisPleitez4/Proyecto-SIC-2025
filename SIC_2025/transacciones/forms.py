from django import forms
from .models import Transaccion, Movimiento
from datetime import date
from decimal import Decimal, ROUND_DOWN


class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = ['descripcion','fecha','monto']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class':'form-control'}),
            'fecha': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step':'0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definimos un vector de campos que queremos requerir
        campos_requeridos = ['descripcion', 'fecha', 'monto']
        for campo in campos_requeridos:
            self.fields[campo].required = True
            self.fields[campo].error_messages = {'required': f'El campo {campo} es obligatorio. Porfavor, ingréselo.'}

    # Validación adicional para monto > 0
    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is None or monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a 0")

        # Validar que tenga como máximo 2 decimales
        monto_decimal = Decimal(monto)
        if monto_decimal.as_tuple().exponent < -2:  # más de 2 decimales
            raise forms.ValidationError("El monto no puede tener más de 2 decimales")

        # Opcional: redondear a 2 decimales antes de guardar
        return monto_decimal.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    
    # Validación para fecha
    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha is None:
            return fecha  # ya se valida con required
        inicio_anio = date(date.today().year, 1, 1)
        limite_max = date(2100, 12, 31)
        if fecha < inicio_anio or fecha > limite_max:
            raise forms.ValidationError(f"La fecha debe estar entre {inicio_anio} y {limite_max}")
        return fecha

class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = [ 'cuenta', 'monto', 'tipo']
        widgets = {
            'cuenta': forms.Select(attrs={'class':'form-select'}),
            'monto': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'tipo': forms.Select(attrs={'class':'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definimos un vector de campos que queremos requerir
        campos_requeridos = ['cuenta', 'monto', 'tipo']
        for campo in campos_requeridos:
            self.fields[campo].required = True
            self.fields[campo].error_messages = {'required': f'El campo {campo} es obligatorio. Porfavor, ingréselo.'}
    
    # Validación adicional para monto > 0
    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is None or monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a 0")

        # Validar que tenga como máximo 2 decimales
        monto_decimal = Decimal(monto)
        if monto_decimal.as_tuple().exponent < -2:  # más de 2 decimales
            raise forms.ValidationError("El monto no puede tener más de 2 decimales")

        # Opcional: redondear a 2 decimales antes de guardar
        return monto_decimal.quantize(Decimal('0.01'), rounding=ROUND_DOWN) 
