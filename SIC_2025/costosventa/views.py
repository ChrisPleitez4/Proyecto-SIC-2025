from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from puestos.models import Puesto
from transacciones.models import Transaccion, Movimiento
from cuentas.models import Cuenta

def calcular_costo(request):
    if request.method == 'POST':
        data = request.POST
        try:
            horas_persona = Decimal(str(data.get('horas_persona', '0')).strip() or '0')
        except:
            horas_persona = Decimal('0')

        puestos = eval(data.get('puestos', '[]'))  # lista de dicts
        cifs = eval(data.get('cifs', '[]'))        # lista de dicts

        # Cálculos
        total_mod = sum(
            Decimal(p['salarioHora']) * Decimal(p['cantidad']) * horas_persona
            for p in puestos
        )

        total_cif = sum(Decimal(c['monto']) for c in cifs)
        total_personas = sum(Decimal(p['cantidad']) for p in puestos)

        total_horas_mes = total_personas * 8 * 5 * 4  # horas trabajadas al mes
        tasa_cif = (total_cif / total_horas_mes) if total_horas_mes > 0 else 0

        total_horas_proyecto = total_personas * horas_persona
        total_cif_proyecto = total_horas_proyecto * tasa_cif

        variacion = (total_mod + total_cif_proyecto) * Decimal('0.30')
        costo_produccion = total_mod + total_cif_proyecto + variacion
        utilidad = costo_produccion * Decimal('0.25')
        precio_venta = costo_produccion + utilidad
        anticipo = precio_venta * Decimal('0.25')
        iva = precio_venta * Decimal('0.13')
        anticipo_total = anticipo + iva

        return JsonResponse({
            'total_mod': float(total_mod),
            'total_cif': float(total_cif),
            'tasa_cif': float(tasa_cif),
            'total_cif_proyecto': float(total_cif_proyecto),
            'variacion': float(variacion),
            'costo_produccion': float(costo_produccion),
            'utilidad': float(utilidad),
            'precio_venta': float(precio_venta),
            'anticipo': float(anticipo),
            'iva': float(iva),
            'anticipo_total': float(anticipo_total)
        })
    else:
        puestos = Puesto.objects.all()
        return render(request, 'costosventa.html', {'puestos': puestos})

def guardar_anticipo(request):
    if request.method == 'POST':
        monto_caja = Decimal(request.POST.get('anticipo_total', 0))
        monto_anticipo = Decimal(request.POST.get('anticipo', 0))
        monto_iva = Decimal(request.POST.get('iva', 0))
        precio_venta = Decimal(request.POST.get('precio_venta', 0))

        # Cuentas involucradas
        cuenta_caja = Cuenta.objects.get(nombreCuenta="Caja")
        cuenta_anticipo = Cuenta.objects.get(nombreCuenta="Anticipo de clientes")
        cuenta_iva = Cuenta.objects.get(nombreCuenta="Retenciones por pagar (Débito Fiscal)")

        descripcion = f"Anticipo del proyecto con un total de ${precio_venta} estimado."

        transaccion = Transaccion.objects.create(
            descripcion=descripcion,
            fecha=timezone.now(),
            monto=monto_caja
        )

        # Movimiento Deudor (Caja)
        Movimiento.objects.create(
            monto=monto_caja,
            tipo=True,  # Deudora
            cuenta=cuenta_caja,
            transaccion=transaccion
        )

        # Movimiento Acreedor (Anticipo de clientes)
        Movimiento.objects.create(
            monto=monto_anticipo,
            tipo=False,  # Acreedora
            cuenta=cuenta_anticipo,
            transaccion=transaccion
        )

        # Movimiento iva (Anticipo de clientes)
        Movimiento.objects.create(
            monto=monto_iva,
            tipo=False,  # Acreedora
            cuenta=cuenta_iva,
            transaccion=transaccion
        )

        return JsonResponse({'mensaje': 'Anticipo guardado correctamente.'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)