from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .models import Transaccion, Movimiento
from .forms import TransaccionForm, MovimientoForm

def transacciones_vista(request):
    transaccion_form = TransaccionForm(request.POST or None)
    movimiento_form = MovimientoForm()  # solo para el modal (sin POST inicial)
    transacciones = Transaccion.objects.all().order_by('-fecha')

    if request.method == 'POST':
        # Crear transacción
        if 'crear_transaccion' in request.POST:
            transaccion_form = TransaccionForm(request.POST)
            if transaccion_form.is_valid():
                transaccion_form.save()
                return redirect('transacciones')

        # Agregar movimiento
        elif 'agregar_movimiento' in request.POST:
            transaccion_id = request.POST.get('transaccion_id')
            transaccion = get_object_or_404(Transaccion, id=transaccion_id)

            # Creamos un dict con los datos del movimiento
            movimiento_data = {
                'transaccion': transaccion.id,
                'cuenta': request.POST.get('cuenta'),
                'monto': request.POST.get('monto'),
                'tipo': request.POST.get('tipo'),
            }

            movimiento_form = MovimientoForm(movimiento_data)
            if movimiento_form.is_valid():
                with transaction.atomic():
                    movimiento = movimiento_form.save()
                    #Actualizar la cuenta según tipo booleano
                    cuenta = movimiento.cuenta
                    if movimiento.tipo:  # True = deudora
                        cuenta.debe += movimiento.monto
                    else:  # False = acreedora
                        cuenta.haber += movimiento.monto

                    cuenta.save()
                return redirect('transacciones')

    context = {
        'transaccion_form': transaccion_form,
        'movimiento_form': movimiento_form,
        'transacciones': transacciones,
    }
    return render(request, 'transacciones/transacciones.html', context)
