from django.shortcuts import render, redirect
from .models import TipoCuenta
from .forms import CuentaForm

def lista_cuentas(request):
    tipos = TipoCuenta.objects.prefetch_related('subtipos__cuentas').all()

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
