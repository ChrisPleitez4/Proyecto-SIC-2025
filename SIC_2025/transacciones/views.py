from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .models import Transaccion, Movimiento
from .forms import TransaccionForm, MovimientoForm
from django.core.paginator import Paginator
from periodos.models import PeriodoContable
from django.db.models import Sum, Case, When, DecimalField, Value
from cuentas.models import Cuenta
from decimal import Decimal


def transacciones_vista(request):
    transaccion_form = TransaccionForm(request.POST or None)
    movimiento_form = MovimientoForm()  # solo para el modal (sin POST inicial)
    periodo_activo = PeriodoContable.objects.filter(activo=True).first()
    if periodo_activo:
        transacciones = (
        Transaccion.objects
        .filter(periodo=periodo_activo)
        .annotate(
            total_debe=Sum(
                Case(
                    When(movimientos__tipo=True, then='movimientos__monto'),
                    default=Value(0),
                    output_field=DecimalField()
                )
            ),
            total_haber=Sum(
                Case(
                    When(movimientos__tipo=False, then='movimientos__monto'),
                    default=Value(0),
                    output_field=DecimalField()
                )
            )
        )
        .order_by('id')
    )
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
                    print("Cuenta:", cuenta.codCuenta, "¿Es ingreso?", cuenta.es_ingreso(), "Tipo:", movimiento.tipo)
                    if cuenta.es_ingreso() and movimiento.tipo == False:
                        print(">>> ENTRÓ AL BLOQUE DE INGRESO CON IVA <<<")
                        monto = movimiento.monto
                        iva = monto * Decimal('0.13')
                        total = monto + iva

                        # --- 1️ Cuenta de Ingreso ---
                        cuenta.haber += monto
                        cuenta.save()

                        # --- 2️ IVA por pagar (2103) ---
                        cIva = Cuenta.objects.get(codCuenta='2103')
                        cIva.haber += iva
                        cIva.save()
                        # Crear movimiento del IVA
                        Movimiento.objects.create(
                            cuenta=cIva,
                            transaccion=transaccion,
                            monto=iva,
                            tipo=False  # Haber
                        )

                        # --- 3️⃣ Caja (1101) ---
                        cCaja = Cuenta.objects.get(codCuenta='1101')
                        cCaja.debe += total
                        cCaja.save()
                        # Crear movimiento de la Caja
                        Movimiento.objects.create(
                            cuenta=cCaja,
                            transaccion=transaccion,
                            monto=total,
                            tipo=True  # Debe
                    )
                    else:
                        print(">>> ENTRÓ AL BLOQUE NORNMAL <<<")
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
