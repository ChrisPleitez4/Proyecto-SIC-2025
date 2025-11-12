from django.shortcuts import render, redirect
from .models import TipoCuenta,Cuenta
from .forms import CuentaForm
from django.db.models import Prefetch




def lista_cuentas(request):
    cuentas_ordenadas = Prefetch('cuentas', queryset=Cuenta.objects.order_by('codCuenta'))
    #tipos = TipoCuenta.objects.prefetch_related('subtipos__cuentas').all()
    tipos = TipoCuenta.objects.prefetch_related(Prefetch('subtipos__cuentas', queryset=Cuenta.objects.order_by('codCuenta')))

    if request.method == 'POST':
        form = CuentaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_cuentas')
        else:
            # Guardar solo los datos, no los errores
            request.session['form_data'] = request.POST
            return redirect('lista_cuentas')

    else:
        if 'form_data' in request.session:
            form_data = request.session.pop('form_data')
            form = CuentaForm(form_data)
            abrir_modal = True
        else:
            form = CuentaForm()
            abrir_modal = False

    return render(request, 'cuentas/lista_cuentas.html', {
        'tipos': tipos,
        'form': form,
        'abrir_modal': abrir_modal
    })
    
def index(request):
    return render(request, 'index.html')
