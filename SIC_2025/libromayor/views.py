from collections import defaultdict
from django.shortcuts import render
from django.http import JsonResponse
from cuentas.models import Cuenta
from transacciones.models import Movimiento, Transaccion

def libro_mayor(request):
    # Obtener todas las cuentas con sus relaciones para evitar consultas repetidas
    cuentas = Cuenta.objects.select_related('subTipoCuenta', 'subTipoCuenta__tipoCuenta').all().order_by(
        'subTipoCuenta__tipoCuenta__codTipoCuenta',
        'subTipoCuenta__codSubTipoCuenta',
        'codCuenta'
    )

    # Agrupar cuentas por tipo y subtipo
    data_dict = defaultdict(lambda: defaultdict(list))

    for cuenta in cuentas:
        # Movimientos de la cuenta
        movimientos = Movimiento.objects.filter(cuenta=cuenta).select_related('transaccion').order_by('transaccion__fecha', 'id')

        saldo = 0
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

    return render(request, 'libromayor.html', {'data': data})


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