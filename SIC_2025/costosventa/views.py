from decimal import Decimal, InvalidOperation
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from puestos.models import Puesto
from transacciones.models import Transaccion, Movimiento
from cuentas.models import Cuenta


def _to_decimal(value, default='0'):
    """
    Convierte un string/número a Decimal de forma segura.
    Si falla, retorna Decimal(default).
    """
    try:
        if value is None:
            return Decimal(default)
        return Decimal(str(value).strip() or default)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def calcular_costo(request):
    """
    GET  -> Renderiza el template con el catálogo de puestos.
    POST -> Recibe horas_persona, puestos[], cifs[] y devuelve cálculos en JSON.
    """
    if request.method == 'POST':
        data = request.POST

        # Horas por persona (puede venir con decimales desde UCP)
        horas_persona = _to_decimal(data.get('horas_persona'), '0')

        # Listas (JSON) desde el front: evitar eval, usar json.loads con fallback.
        try:
            puestos = json.loads(data.get('puestos', '[]'))  # [{id, nombre, salarioHora, cantidad, costoTotal}]
        except json.JSONDecodeError:
            puestos = []

        try:
            cifs = json.loads(data.get('cifs', '[]'))        # [{descripcion, monto}]
        except json.JSONDecodeError:
            cifs = []

        # Cálculo de Mano de Obra Directa (MOD)
        total_mod = Decimal('0')
        total_personas = Decimal('0')
        for p in puestos:
            salario_hora = _to_decimal(p.get('salarioHora'), '0')
            cantidad = _to_decimal(p.get('cantidad'), '0')
            total_mod += salario_hora * cantidad * horas_persona
            total_personas += cantidad

        # Suma de CIF ingresados
        total_cif = Decimal('0')
        for c in cifs:
            total_cif += _to_decimal(c.get('monto'), '0')

        # Tasa CIF mensual: (total CIF mensual) / (horas trabajadas mes)
        # 8h * 5d * 4sem = 160 horas mensuales por persona (aprox)
        horas_mes_por_persona = Decimal('160')
        total_horas_mes = total_personas * horas_mes_por_persona
        tasa_cif = (total_cif / total_horas_mes) if total_horas_mes > 0 else Decimal('0')

        # CIF aplicado al proyecto: (personas * horas del proyecto * tasa_cif)
        total_horas_proyecto = total_personas * horas_persona
        total_cif_proyecto = total_horas_proyecto * tasa_cif

        # Variación 30%, Utilidad 25%, Precio, etc.
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
            'anticipo_total': float(anticipo_total),
        })

    # GET
    puestos = Puesto.objects.all()
    return render(request, 'costosventa.html', {'puestos': puestos})


def guardar_anticipo(request):
    """
    Guarda el anticipo (25%) + IVA del precio de venta como una transacción:
     - Debe:  Caja (por el anticipo total cobrado)
     - Haber: Anticipo de clientes (anticipo sin IVA)
     - Haber: Débito fiscal (IVA del anticipo)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    monto_caja = _to_decimal(request.POST.get('anticipo_total'), '0')
    monto_anticipo = _to_decimal(request.POST.get('anticipo'), '0')
    monto_iva = _to_decimal(request.POST.get('iva'), '0')
    precio_venta = _to_decimal(request.POST.get('precio_venta'), '0')

    # Validación mínima
    if monto_caja <= 0 or monto_anticipo <= 0 or monto_iva < 0:
        return JsonResponse({'error': 'Montos inválidos para registrar el anticipo.'}, status=400)

    # Cuentas involucradas (asegúrate que existan con esos nombres)
    try:
        cuenta_caja = Cuenta.objects.get(nombreCuenta="Caja")
        cuenta_anticipo = Cuenta.objects.get(nombreCuenta="Anticipo de clientes")
        cuenta_iva = Cuenta.objects.get(nombreCuenta="Retenciones por pagar (Débito Fiscal)")
    except Cuenta.DoesNotExist as e:
        return JsonResponse({'error': f'Falta la cuenta: {e}'}, status=400)

    descripcion = f"Anticipo del proyecto con un total estimado de ${precio_venta}."

    transaccion = Transaccion.objects.create(
        descripcion=descripcion,
        fecha=timezone.now(),
        monto=monto_caja
    )

    # Debe: Caja
    Movimiento.objects.create(
        monto=monto_caja,
        tipo=True,  # Deudora
        cuenta=cuenta_caja,
        transaccion=transaccion
    )
    #actualizar cuenta Aldair0t
    cuenta_caja.debe += monto_caja
    cuenta_caja.save()

    # Haber: Anticipo de clientes
    Movimiento.objects.create(
        monto=monto_anticipo,
        tipo=False,  # Acreedora
        cuenta=cuenta_anticipo,
        transaccion=transaccion
    )
    cuenta_anticipo.haber += monto_anticipo
    cuenta_anticipo.save()

    # Haber: Débito fiscal (IVA)
    Movimiento.objects.create(
        monto=monto_iva,
        tipo=False,  # Acreedora
        cuenta=cuenta_iva,
        transaccion=transaccion
    )
    cuenta_iva.haber += monto_iva
    cuenta_iva.save()

    return JsonResponse({'mensaje': 'Anticipo guardado correctamente.'})
