from django import forms
from .models import Cuenta, SubTipoCuenta
import re


class CuentaForm(forms.ModelForm):
    codCuenta = forms.CharField(
        max_length=10,
        label="Código de Cuenta",
        error_messages={
            'required': 'El código de cuenta es obligatorio.',
        }
    )
    nombreCuenta = forms.CharField(
        max_length=20,  # Limite de 20 caracteres
        label="Nombre de la Cuenta",
        error_messages={
            'required': 'El nombre de la cuenta es obligatorio.',
            'max_length': 'El nombre de la cuenta no puede superar los 20 caracteres.',
        }
    )
    subTipoCuenta = forms.ModelChoiceField(
        queryset=SubTipoCuenta.objects.all(),
        label="Subtipo de Cuenta",
        empty_label="Seleccione un subtipo",
        error_messages={
            'required': 'Debe seleccionar un subtipo de cuenta.',
        }
    )

    class Meta:
        model = Cuenta
        fields = ['codCuenta', 'nombreCuenta', 'subTipoCuenta']

    def clean_codCuenta(self):
        cod = self.cleaned_data.get('codCuenta')
        
        if not cod.isdigit():
            raise forms.ValidationError("El código de cuenta debe contener solo números.")
        if len(cod) > 4:
            raise forms.ValidationError("El código de cuenta no puede tener más de 4 digitos numericos.")
        if cod and Cuenta.objects.filter(codCuenta=cod).exists():
            raise forms.ValidationError("Ya existe una cuenta con este código.")
        return cod

    def clean_nombreCuenta(self):
        nombre = self.cleaned_data.get('nombreCuenta')
        if any(char.isdigit() for char in nombre):
            raise forms.ValidationError("El nombre de la cuenta no puede contener números.")
        if len(nombre) > 20:
            raise forms.ValidationError("El nombre de la cuenta no puede tener más de 20 caracteres.")
        return nombre

    def clean(self):
        cleaned_data = super().clean()
        cod = cleaned_data.get('codCuenta')
        subtipo = cleaned_data.get('subTipoCuenta')

        # Validación: el código debe empezar con el código del subtipo
        if cod and subtipo:
            cod_subtipo = str(subtipo.codSubTipoCuenta)
            if not cod.startswith(cod_subtipo):
                self.add_error(
                    'codCuenta',
                    f"El código de cuenta NO corresponde al subtipo de cuenta ({cod_subtipo})."
                )
