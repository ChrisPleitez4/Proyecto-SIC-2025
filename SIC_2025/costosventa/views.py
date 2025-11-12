from decimal import Decimal, InvalidOperation
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from puestos.models import Puesto
from transacciones.models import Transaccion, Movimiento
from cuentas.models import Cuenta
from periodos.models import PeriodoContable # Importar el modelo de Periodo Contable


def _to_decimal(value, default='0'):
    # ... (función to_decimal se mantiene igual)
    try:
        if value is None:
            return Decimal(default)
        return Decimal(str(value).strip() or default)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def calcular_costo(request):
    """
    GET  -> Renderiza el template SÓLO con puestos NO administrativos.
    POST -> Recibe datos y realiza cálculos, distinguiendo MOD y CIF por el atributo 'administrativo'.
    """
    if request.method == 'POST':
        data = request.POST

        # Horas por persona (puede venir con decimales desde UCP)
        horas_persona = _to_decimal(data.get('horas_persona'), '0')

        try:
            puestos_json = json.loads(data.get('puestos', '[]'))  # Puestos seleccionados manualmente
        except json.JSONDecodeError:
            puestos_json = []

        try:
            cifs_manuales = json.loads(data.get('cifs', '[]'))      # CIFs manuales
        except json.JSONDecodeError:
            cifs_manuales = []

        # CÁLCULO DE MANO DE OBRA DIRECTA (MOD) Y CIF AUTOMÁTICOS

        total_mod = Decimal('0')
        total_personas_directas = Decimal('0')
        total_cif_salarios_admin = Decimal('0')

        # Obtener los IDs (idPuesto) de los puestos que vienen del formulario
        puesto_ids = [p.get('id') for p in puestos_json]
        
        # Obtener los puestos del formulario desde la bd
        puestos_en_db = Puesto.objects.filter(idPuesto__in=puesto_ids)

        for p_data in puestos_json:
            # Buscar el objeto Puesto real usando el idPuesto
            p_db = next((p for p in puestos_en_db if p.idPuesto == int(p_data.get('id'))), None)
            
            if not p_db:
                continue

            # Obtener datos
            cantidad = _to_decimal(p_data.get('cantidad'), '0')
            salario_hora = _to_decimal(p_data.get('salarioHora'), '0')

            # Verificación del atributo administrativo para diferenciar MOD/CIF
            if hasattr(p_db, 'administrativo') and p_db.administrativo:
                # Si es administrativo, el salario MENSUAL va a CIF
                salario_mes = _to_decimal(p_db.salarioMesPuesto, '0')
                total_cif_salarios_admin += salario_mes * cantidad
            else:
                # Si es directo, el costo va a MOD
                total_mod += salario_hora * cantidad * horas_persona
                total_personas_directas += cantidad

        #CIF FIJOS PREDEFINIDOS
        
        ids_cif_admin_ya_incluidos = [p.idPuesto for p in puestos_en_db if p.administrativo]
        
        cif_admin_faltantes = Puesto.objects.filter(
            administrativo=True
        ).exclude(
            idPuesto__in=ids_cif_admin_ya_incluidos
        )
        
        for p_admin in cif_admin_faltantes:
            # Asumimos una cantidad de 1
            salario_mes = _to_decimal(p_admin.salarioMesPuesto, '0')
            total_cif_salarios_admin += salario_mes * Decimal('1') 


        #CIF Fijos.
        cif_fijos_predefinidos = [
            {'descripcion': 'Depreciación de mobiliario', 'monto': Decimal('26.08')},
            {'descripcion': 'Depreciación de equipo de computo y red', 'monto': Decimal('224.88')},
            {'descripcion': 'Depreciación de otros equipos', 'monto': Decimal('4.46')},
            {'descripcion': 'Amortización de software', 'monto': Decimal('41.67')},
            {'descripcion': 'Papeleria y suministros', 'monto': Decimal('72.50')},
            {'descripcion': 'Software y herramientas digitales', 'monto': Decimal('955.00')},
            {'descripcion': 'Servidor de nube', 'monto': Decimal('20.00')},
            {'descripcion': 'Alquiler de local', 'monto': Decimal('1500.00')},
            {'descripcion': 'Servicio de internet', 'monto': Decimal('50.00')},
            {'descripcion': 'Servicio de agua potable', 'monto': Decimal('30.00')},
            {'descripcion': 'Servicio de energia eléctrica', 'monto': Decimal('110.00')},

        ]
        
        total_cif_fijos = sum(c.get('monto') for c in cif_fijos_predefinidos)

        #SUMA DE TODOS LOS CIF

        total_cif_manuales = Decimal('0')
        for c in cifs_manuales:
            total_cif_manuales += _to_decimal(c.get('monto'), '0')

        # Total CIF Mensual (Salarios + Fijos + Manuales)
        total_cif = total_cif_salarios_admin + total_cif_fijos + total_cif_manuales

        #CÁLCULOS FINALES 
        horas_mes_por_persona = Decimal('160')
        total_horas_mes_mod = total_personas_directas * horas_mes_por_persona
        
        tasa_cif = (total_cif / total_horas_mes_mod) if total_horas_mes_mod > 0 else Decimal('0')

        total_horas_proyecto = total_personas_directas * horas_persona
        total_cif_proyecto = total_horas_proyecto * tasa_cif

        variacion = (total_mod + total_cif_proyecto) * Decimal('0.30')
        costo_produccion = total_mod + total_cif_proyecto + variacion
        utilidad = costo_produccion * Decimal('0.25')
        precio_venta = costo_produccion + utilidad
        anticipo = precio_venta * Decimal('0.25')
        
        iva = anticipo * Decimal('0.13')
        anticipo_total = anticipo + iva
        diferencia = precio_venta - anticipo

        # Retornar CIF
        cifs_aplicados = []
        if total_cif_salarios_admin > 0:
             cifs_aplicados.append({'descripcion': 'Salarios de puestos administrativo', 'monto': float(total_cif_salarios_admin)})
        
        # Se agregan los CIF fijos y manuales
        cifs_aplicados.extend([{'descripcion': c['descripcion'], 'monto': float(c['monto'])} for c in cif_fijos_predefinidos])
        cifs_aplicados.extend([{'descripcion': c['descripcion'], 'monto': float(c['monto'])} for c in cifs_manuales])
        
        
        return JsonResponse({
            'total_mod': float(total_mod),
            'total_cif': float(total_cif), # Total CIF Mensual Global
            'tasa_cif': float(tasa_cif),
            'total_cif_proyecto': float(total_cif_proyecto), # CIF aplicado al proyecto
            'variacion': float(variacion),
            'costo_produccion': float(costo_produccion),
            'utilidad': float(utilidad),
            'precio_venta': float(precio_venta),
            'anticipo': float(anticipo),
            'iva': float(iva),
            'anticipo_total': float(anticipo_total),
            'diferencia': float(diferencia),
            'cifs_aplicados': cifs_aplicados 
        })

    # Solo los puestos de Mano de Obra Directa deben aparecer en el modal.
    puestos = Puesto.objects.filter(administrativo=False).order_by('nombrePuesto')
    return render(request, 'costosventa.html', {'puestos': puestos})

def guardar_anticipo(request):
    """
    Guarda el anticipo (25%) + IVA del precio de venta como una transacción,
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'error': 'Método no permitido'})

    # Validación de nombre del proyecto
    nombre_proyecto = request.POST.get('nombre_proyecto', '').strip()
    if not nombre_proyecto:
        return JsonResponse({
            'status': 'error',
            'error': 'El nombre del proyecto no puede estar vacío.'
        })
    
    # Buscamos si existe al menos un período contable con activo=True
    if not PeriodoContable.objects.filter(activo=True).exists():
        return JsonResponse({
            'status': 'error',
            'error': 'No se puede guardar el anticipo. No hay un período contable activo.'
        })
    
    #PROCESAMIENTO DE ANTICIPO

    monto_anticipo = _to_decimal(request.POST.get('anticipo'), '0')
    monto_iva = _to_decimal(request.POST.get('iva'), '0')
    precio_venta = _to_decimal(request.POST.get('precio_venta'), '0')
    diferencia = _to_decimal(request.POST.get('diferencia'), '0')

    monto_caja = monto_anticipo + monto_iva

    # Validación mínima
    if monto_caja <= 0 or monto_anticipo <= 0 or monto_iva < 0:
        return JsonResponse({
            'status': 'error',
            'error': 'Montos inválidos para registrar el anticipo.'})

    # Cuentas involucradas
    try:
        cuenta_caja = Cuenta.objects.get(nombreCuenta="Caja")
        cuenta_anticipo = Cuenta.objects.get(nombreCuenta="Anticipo de clientes")
        cuenta_iva = Cuenta.objects.get(nombreCuenta="Retenciones por pagar (Débito Fiscal)")
    except Cuenta.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'error': 'Error en la configuración de cuentas contables.'})

    descripcion = (
        f"Anticipo del proyecto: {nombre_proyecto} con precio de venta ${precio_venta}); "
        f"Monto pendiente de pago: ${diferencia}."
    )

    #CREACIÓN DE TRANSACCIÓN Y MOVIMIENTOS
    
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
    # actualizar cuenta
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

    return JsonResponse({
        'status': 'success', # Indicador de éxito
        'mensaje': 'Anticipo guardado correctamente.'
    })