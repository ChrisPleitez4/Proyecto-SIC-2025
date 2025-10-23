from django.shortcuts import render
from .models import TipoCuenta, SubTipoCuenta, Cuenta
# Create your views here.

def lista_cuentas(request):
    tipos = TipoCuenta.objects.prefetch_related('subtipos__cuentas').all()
    return render(request, 'cuentas/lista_cuentas.html',{'tipos':tipos})