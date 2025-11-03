from collections import defaultdict
from django.shortcuts import render
from django.http import JsonResponse
from cuentas.models import Cuenta
from transacciones.models import Movimiento, Transaccion
from periodos.models import PeriodoContable, SaldoCuenta

def libro_mayor(request):
    # Todos los periodos para el dropdown
    periodos = PeriodoContable.objects.order_by('-fecha_inicio')

    # Periodo seleccionado por GET (si no hay, usar último activo)
    periodo_id = request.GET.get('periodo')
    periodo = None
    if periodo_id:
        periodo = PeriodoContable.objects.filter(pk=periodo_id).first()
    if not periodo:
        periodo = PeriodoContable.objects.filter(activo=True).first()

    cuentas = Cuenta.objects.select_related('subTipoCuenta', 'subTipoCuenta__tipoCuenta').all().order_by(
        'subTipoCuenta__tipoCuenta__codTipoCuenta',
        'subTipoCuenta__codSubTipoCuenta',
        'codCuenta'
    )

    data_dict = defaultdict(lambda: defaultdict(list))

    for cuenta in cuentas:
        # Movimientos dentro del periodo
        movimientos = Movimiento.objects.filter(
            cuenta=cuenta,
            transaccion__fecha__gte=periodo.fecha_inicio,
            transaccion__fecha__lte=periodo.fecha_fin
        ).select_related('transaccion').order_by('transaccion__fecha', 'id')

        # SALDO INICIAL: usar SaldoCuenta del periodo anterior si existe
        saldo_inicial_obj = SaldoCuenta.objects.filter(
            cuenta=cuenta,
            periodo__fecha_fin__lt=periodo.fecha_inicio
        ).order_by('-periodo__fecha_fin').first()
        saldo_inicial = saldo_inicial_obj.saldo_final if saldo_inicial_obj else 0

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

    # Convertir defaultdict a lista de diccionarios para template
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