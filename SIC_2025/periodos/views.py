from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
from collections import defaultdict
from django.http import JsonResponse
from .models import PeriodoContable, SaldoCuenta
from .forms import PeriodoContableForm
from cuentas.models import Cuenta
from transacciones.models import Movimiento, Transaccion


# ------------------- PERIODO CONTABLE -------------------

def lista_periodos(request):
    periodos = PeriodoContable.objects.all()
    return render(request, "lista_periodos.html", {"periodos": periodos})


def crear_periodo(request):
    if request.method == "POST":
        form = PeriodoContableForm(request.POST)
        if form.is_valid():
            # Verificar si hay un periodo activo
            if PeriodoContable.objects.filter(activo=True).exists():
                messages.error(request, "Ya existe un periodo activo. Cierre el periodo actual antes de crear uno nuevo.")
                return redirect('lista_periodos')

            # Guardar periodo como activo
            nuevo_periodo = form.save(commit=False)
            nuevo_periodo.activo = True
            nuevo_periodo.save()

            # Inicializar saldos del nuevo periodo con saldos finales del periodo anterior
            inicializar_saldos_nuevo_periodo(nuevo_periodo)

            messages.success(request, "Periodo creado correctamente.")
            return redirect('lista_periodos')
    else:
        form = PeriodoContableForm()
    return render(request, 'crear_periodo.html', {'form': form})


def cerrar_periodo(request, pk):
    periodo = get_object_or_404(PeriodoContable, pk=pk)
    try:
        periodo.cerrar_periodo()
        # Calcular saldos finales al cerrar el periodo y trasladar utilidad
        SaldoCuenta.calcular_saldos_periodo(periodo)
        messages.success(request, "Periodo cerrado correctamente y saldos calculados.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("lista_periodos")


# ------------------- FUNCIONES AUXILIARES -------------------

def inicializar_saldos_nuevo_periodo(periodo):
    """Inicializa los saldos del nuevo periodo tomando el saldo final del periodo anterior"""
    cuentas = Cuenta.objects.all()
    periodo_anterior = PeriodoContable.objects.filter(fecha_fin__lt=periodo.fecha_inicio).order_by('-fecha_fin').first()

    for cuenta in cuentas:
        saldo_inicial = Decimal('0.00')
        if periodo_anterior:
            saldo_anterior_obj = SaldoCuenta.objects.filter(
                cuenta=cuenta,
                periodo=periodo_anterior
            ).first()
            if saldo_anterior_obj:
                saldo_inicial = saldo_anterior_obj.saldo_final

        # Crear el saldo inicial en el nuevo periodo
        SaldoCuenta.objects.update_or_create(
            cuenta=cuenta,
            periodo=periodo,
            defaults={'saldo_final': saldo_inicial}
        )


# ------------------- LIBRO MAYOR -------------------

def libro_mayor(request):
    # Todos los periodos para dropdown
    periodos = PeriodoContable.objects.order_by('-fecha_inicio')

    periodo_id = request.GET.get('periodo')
    if periodo_id:
        try:
            periodo = PeriodoContable.objects.get(pk=periodo_id)
        except PeriodoContable.DoesNotExist:
            periodo = PeriodoContable.objects.filter(activo=True).first()
    else:
        periodo = PeriodoContable.objects.filter(activo=True).first()

    if not periodo:
        return render(request, 'libromayor.html', {
            'data': [],
            'periodos': periodos,
            'periodo_seleccionado': None
        })

    cuentas = Cuenta.objects.select_related('subTipoCuenta', 'subTipoCuenta__tipoCuenta').all().order_by(
        'subTipoCuenta__tipoCuenta__codTipoCuenta',
        'subTipoCuenta__codSubTipoCuenta',
        'codCuenta'
    )

    data_dict = defaultdict(lambda: defaultdict(list))

    for cuenta in cuentas:
        # ===== SALDO INICIAL =====
        saldo_inicial_obj = SaldoCuenta.objects.filter(
            cuenta=cuenta,
            periodo__fecha_fin__lt=periodo.fecha_inicio
        ).order_by('-periodo__fecha_fin').first()
        saldo_inicial = saldo_inicial_obj.saldo_final if saldo_inicial_obj else Decimal('0.00')

        # ===== MOVIMIENTOS DEL PERIODO =====
        movimientos = Movimiento.objects.filter(
            cuenta=cuenta,
            transaccion__fecha__gte=periodo.fecha_inicio,
            transaccion__fecha__lte=periodo.fecha_fin
        ).select_related('transaccion').order_by('transaccion__fecha', 'id')

        saldo = saldo_inicial
        movimientos_data = []

        for mov in movimientos:
            if mov.tipo:  # Debe
                saldo += mov.monto
                debe = float(mov.monto)
                haber = 0.0
            else:        # Haber
                saldo -= mov.monto
                debe = 0.0
                haber = float(mov.monto)

            movimientos_data.append({
                'codigo': mov.transaccion.id,
                'fecha': mov.transaccion.fecha.strftime('%Y-%m-%d'),
                'debe': debe,
                'haber': haber,
                'saldo': float(saldo),
            })

        cuenta_dict = {
            'cuenta': cuenta,
            'saldo_inicial': float(saldo_inicial),
            'movimientos': movimientos_data,
            'saldo_final': float(saldo)
        }

        tipo = cuenta.subTipoCuenta.tipoCuenta
        subtipo = cuenta.subTipoCuenta
        data_dict[tipo][subtipo].append(cuenta_dict)

    # Convertir defaultdict a lista
    data = []
    for tipo_obj, subtipos in data_dict.items():
        subtipo_list = []
        for subtipo_obj, cuentas_list in subtipos.items():
            subtipo_list.append({
                'subtipo': subtipo_obj,
                'cuentas': cuentas_list
            })
        data.append({
            'tipo': tipo_obj,
            'subtipos': subtipo_list
        })

    return render(request, 'libromayor.html', {
        'data': data,
        'periodos': periodos,
        'periodo_seleccionado': periodo
    })


def detalle_transaccion_libromayor(request, transaccion_id):
    try:
        transaccion = Transaccion.objects.get(pk=transaccion_id)
        movimientos = Movimiento.objects.filter(transaccion=transaccion).select_related('cuenta').order_by('id')

        data = {
            'codigo': transaccion.id,
            'fecha': transaccion.fecha.strftime('%Y-%m-%d'),
            'descripcion': transaccion.descripcion,
            'movimientos': [
                {
                    'cuenta': m.cuenta.nombreCuenta,
                    'debe': float(m.monto) if m.tipo else 0.0,
                    'haber': float(m.monto) if not m.tipo else 0.0,
                } for m in movimientos
            ]
        }
        return JsonResponse(data)
    except Transaccion.DoesNotExist:
        return JsonResponse({'error': 'Transacción no encontrada'}, status=404)

