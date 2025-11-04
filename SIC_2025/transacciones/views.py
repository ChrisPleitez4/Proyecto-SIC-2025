from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .models import Transaccion, Movimiento
from .forms import TransaccionForm, MovimientoForm
from django.core.paginator import Paginator
from periodos.models import PeriodoContable

def transacciones_vista(request):
    transaccion_form = TransaccionForm(request.POST or None)
    movimiento_form = MovimientoForm()  # solo para el modal (sin POST inicial)
    periodo_activo = PeriodoContable.objects.filter(activo=True).first()
    if periodo_activo:
        transacciones = Transaccion.objects.filter(periodo =periodo_activo).order_by('id')
    else:
        transacciones = Transaccion.objects.none() #nada porque no hay periodo activo
    # Paginación
    paginator = Paginator(transacciones, 10) # 10 transacciones por página 
    page_number = request.GET.get('page') # obtener la página de la URL 
    page_obj = paginator.get_page(page_number)
    mensaje_exito = None
    mostrar_modal_movimiento = None
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
            # Instanciamos el formulario directamente con request.POST
            movimiento_form = MovimientoForm(request.POST)
            # Creamos un dict con los datos del movimiento
            

            if movimiento_form.is_valid():
                with transaction.atomic():
                    movimiento = movimiento_form.save(commit=False)
                    movimiento.transaccion = transaccion  # asignamos la FK
                    movimiento.save()
                    cuenta = movimiento.cuenta
                    if movimiento.tipo:  # True = deudora
                        cuenta.debe += movimiento.monto
                    else:  # False = acreedora
                        cuenta.haber += movimiento.monto
                    cuenta.save()
                return redirect('transacciones')
            else:
                mostrar_modal_movimiento = transaccion.id  # para reabrir el modal con errores
                # Reiniciamos transaccion_form limpio para que no muestre errores
                transaccion_form = TransaccionForm()
    context = {
        'transaccion_form': transaccion_form,
        'movimiento_form': movimiento_form,
        'page_obj': page_obj,
        'mostrar_modal_movimiento': mostrar_modal_movimiento,
        
    }
    return render(request, 'transacciones/transacciones.html', context)
