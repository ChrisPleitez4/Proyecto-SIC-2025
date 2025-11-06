from collections import defaultdict
from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import messages
from cuentas.models import Cuenta
from transacciones.models import Movimiento, Transaccion
from periodos.models import PeriodoContable


def libro_mayor(request):
    # Todos los periodos para el dropdown
    periodos = PeriodoContable.objects.order_by('-fecha_inicio')

    # Periodo seleccionado por GET (si no hay, usar último activo)
    periodo_id = request.GET.get('periodo')
    periodo = PeriodoContable.objects.filter(pk=periodo_id).first() if periodo_id else None
    if not periodo:
        periodo = PeriodoContable.objects.filter(activo=True).first()

    if not periodo:
        messages.warning(request, "No hay periodos contables activos o cerrados disponibles.")
        return render(request, 'libromayor.html', {
            'data': [], 'periodos': periodos, 'periodo_seleccionado': None
        })

    cuentas = Cuenta.objects.select_related('subTipoCuenta', 'subTipoCuenta__tipoCuenta').all().order_by(
        'subTipoCuenta__tipoCuenta__codTipoCuenta',
        'subTipoCuenta__codSubTipoCuenta',
        'codCuenta'
    )

    data_dict = defaultdict(lambda: defaultdict(list))

    for cuenta in cuentas:
        # ==== SALDO INICIAL ====
        periodo_anterior = PeriodoContable.objects.filter(
            fecha_fin__lt=periodo.fecha_inicio, activo=False
        ).order_by('-fecha_fin').first()

        if periodo_anterior:
            saldo_cuenta = cuenta.saldo_final or Decimal('0.00')
            tipo_saldo_inicial = cuenta.tipo_saldo() if saldo_cuenta != 0 else "Saldo Cero"
            saldo_inicial = abs(saldo_cuenta)
        else:
            saldo_inicial = Decimal('0.00')
            tipo_saldo_inicial = "Saldo Cero"

        # Ajuste de saldo inicial según naturaleza
        saldo = saldo_inicial if tipo_saldo_inicial in ['Deudor', 'Saldo Cero'] else -saldo_inicial

        # ==== MOVIMIENTOS DEL PERIODO ACTUAL ====
        movimientos = Movimiento.objects.filter(
            cuenta=cuenta,
            transaccion__periodo=periodo
        ).select_related('transaccion').order_by('transaccion__fecha', 'id')

        movimientos_data = []
        for mov in movimientos:
            if mov.tipo:  # Debe
                saldo += mov.monto
                debe = float(mov.monto)
                haber = 0.0
            else:  # Haber
                saldo -= mov.monto
                debe = 0.0
                haber = float(mov.monto)

            movimientos_data.append({
                'codigo': mov.transaccion.nro_transaccion,
                'fecha': mov.transaccion.fecha.strftime('%Y-%m-%d'),
                'debe': debe,
                'haber': haber,
                'saldo': float(saldo),
            })

        # ==== SALDO FINAL ====
        tipo_saldo_final = "Deudor" if saldo > 0 else ("Acreedor" if saldo < 0 else "Saldo Cero")
        saldo_final = abs(saldo)

        cuenta_dict = {
            'cuenta': cuenta,
            'saldo_inicial': f"{float(saldo_inicial):,.2f} ({tipo_saldo_inicial})",
            'movimientos': movimientos_data,
            'saldo_final': f"{float(saldo_final):,.2f} ({tipo_saldo_final})"
        }

        tipo = cuenta.subTipoCuenta.tipoCuenta
        subtipo = cuenta.subTipoCuenta
        data_dict[tipo][subtipo].append(cuenta_dict)

    # Convertir defaultdict a lista de diccionarios para template
    data = []
    for tipo_obj, subtipos in data_dict.items():
        subtipo_list = []
        for subtipo_obj, cuentas_list in subtipos.items():
            subtipo_list.append({'subtipo': subtipo_obj, 'cuentas': cuentas_list})
        data.append({'tipo': tipo_obj, 'subtipos': subtipo_list})

    return render(request, 'libromayor.html', {
        'data': data,
        'periodos': periodos,
        'periodo_seleccionado': periodo
    })


# ======================= DETALLE DE TRANSACCIÓN =======================
def detalle_transaccion_libromayor(request):
    # Leer nro_transaccion y periodo desde GET
    nro = request.GET.get('nro')
    periodo_id = request.GET.get('periodo')

    if not nro or not periodo_id:
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)

    try:
        transaccion = Transaccion.objects.get(periodo_id=periodo_id, nro_transaccion=nro)
        movimientos = transaccion.movimientos.select_related('cuenta').order_by('id')

        data = {
            'codigo': transaccion.nro_transaccion,
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