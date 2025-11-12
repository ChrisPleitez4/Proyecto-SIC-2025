from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from decimal import Decimal, getcontext
from datetime import date
import locale

from periodos.models import PeriodoContable
from cuentas.models import Cuenta
from transacciones.models import Movimiento

# Configurar precisión decimal
getcontext().prec = 18

# Locale español (para nombres de meses)
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain')
    except:
        pass


def estados_financieros(request):
    """
    Calcula y muestra los estados financieros para el periodo activo
    o para un periodo específico pasado por parámetro (periodo_id).
    """
    
    #Obtener Periodos Disponibles y Periodo a Analizar
    periodos_disponibles = PeriodoContable.objects.all().order_by('-fecha_fin')
    
    if not periodos_disponibles.exists():
        messages.error(request, "No existen períodos contables registrados.")
        return render(request, "estados.html", {"sin_periodo": True})

    periodo_id = request.GET.get('periodo_id')
    
    if periodo_id:
        periodo_activo = get_object_or_404(PeriodoContable, id=periodo_id)
    else:
        periodo_activo = periodos_disponibles.filter(activo=True).first() or periodos_disponibles.first()

    if not periodo_activo:
        messages.error(request, "Error: No se pudo determinar el periodo a mostrar.")
        return render(request, "estados.html", {"sin_periodo": True})

    fecha_inicio = periodo_activo.fecha_inicio
    fecha_fin = periodo_activo.fecha_fin
    cuentas = Cuenta.objects.select_related('subTipoCuenta__tipoCuenta').all()
    
    #Buscar el periodo anterior
    periodo_anterior = PeriodoContable.objects.filter(
        fecha_fin__lt=periodo_activo.fecha_inicio, activo=False
    ).order_by('-fecha_fin').first()
    
    # Determinar si estamos en el primer período (sin período anterior)
    es_primer_periodo = not periodo_anterior
    
    # Calcular debe/haber con saldo inicial + movimientos del periodo
    for cuenta in cuentas:
        tipo = cuenta.subTipoCuenta.tipoCuenta.codTipoCuenta[0]
        
        # Inicialización de Saldo Inicial
        saldo_inicial = Decimal('0.00')
        
        # Solo cargar saldo_final si NO es el primer periodo y NO es cuenta de resultado
        if tipo in ['1', '2', '3'] and not es_primer_periodo:
            # Si NO es cuenta de resultado Y SÍ hay un periodo anterior
            saldo_inicial = cuenta.saldo_final or Decimal('0.00')

        #Reiniciar debe y haber
        cuenta.debe = Decimal('0.00')
        cuenta.haber = Decimal('0.00')

        # Cargar saldo inicial según naturaleza
        if tipo == '1':    # Activo → saldo deudor
            if saldo_inicial > 0:
                cuenta.debe = saldo_inicial
            elif saldo_inicial < 0:
                cuenta.haber = abs(saldo_inicial)
        elif tipo in ['2', '3']:  # Pasivo o Capital → saldo acreedor
            if saldo_inicial > 0:
                cuenta.haber = saldo_inicial
            elif saldo_inicial < 0:
                cuenta.debe = abs(saldo_inicial)

        # Sumar movimientos del periodo
        movimientos = Movimiento.objects.filter(
            cuenta=cuenta,
            transaccion__fecha__range=[fecha_inicio, fecha_fin]
        )

        cuenta.debe += sum(m.monto for m in movimientos if m.tipo) or Decimal('0.00')
        cuenta.haber += sum(m.monto for m in movimientos if not m.tipo) or Decimal('0.00')

        # Cálculo del Saldo Final del Período
        if tipo in ['1', '4']: # Activo y Gasto (Naturaleza Deudora)
            cuenta.saldo_calculado = cuenta.debe - cuenta.haber
        elif tipo in ['2', '3', '5']: # Pasivo, Capital e Ingreso (Naturaleza Acreedora)
            cuenta.saldo_calculado = cuenta.haber - cuenta.debe
        else:
             cuenta.saldo_calculado = Decimal('0.00')
             
        # Tipo de saldo calculado
        if cuenta.saldo_calculado > 0:
            cuenta.tipo_saldo_calculado = 'Acreedor' if tipo in ['2', '3', '5'] else 'Deudor'
        elif cuenta.saldo_calculado < 0:
            cuenta.tipo_saldo_calculado = 'Deudor' if tipo in ['2', '3', '5'] else 'Acreedor'
        else:
            cuenta.tipo_saldo_calculado = 'Saldo Cero'



    # Estado de Resultados 
    ingresos = [c for c in cuentas if c.subTipoCuenta.tipoCuenta.codTipoCuenta.startswith('5')]
    gastos = [c for c in cuentas if c.subTipoCuenta.tipoCuenta.codTipoCuenta.startswith('4')]

    # Ingresos (Acreedor) y Gastos (Deudor) ya están calculados con signo positivo.
    total_ingresos = sum(c.saldo_calculado for c in ingresos)
    total_gastos = sum(c.saldo_calculado for c in gastos)
    
    utilidad_bruta = total_ingresos - total_gastos

    impuesto = Decimal('0.00') 
    utilidad_neta = utilidad_bruta

    # Estado de Capital
    capital_cuenta = next((c for c in cuentas if c.codCuenta == '3101'), None) 
    
    # Capital Inicial: Saldo de la cuenta 3101 al inicio del periodo (0 para periodo #1, o saldo final anterior)
    capital_inicial = Decimal('0.00')
    if capital_cuenta:
        # El saldo inicial (solo Debe/Haber) se determinó en 2.3
        capital_inicial = capital_cuenta.haber - capital_cuenta.debe 

    # Capital Social: El saldo inicial de Capital + movimientos de Capital del periodo.
    # En el Periodo #1, esto es el monto de la Transacción #1.
    capital_social = capital_cuenta.saldo_calculado.quantize(Decimal('0.01')) if capital_cuenta else Decimal('0.00')
    
    # Si capital_social ya incluye los movimientos del periodo, solo sumamos la utilidad.
    capital_final = (capital_social + utilidad_bruta).quantize(Decimal('0.01'))
    
    # Balance General
    activos = [c for c in cuentas if c.subTipoCuenta.tipoCuenta.codTipoCuenta.startswith('1')]
    pasivos = [c for c in cuentas if c.subTipoCuenta.tipoCuenta.codTipoCuenta.startswith('2')]

    def procesar_cuentas(qs):
        filas = []
        for c in qs:
            filas.append({
                'cod': c.codCuenta,
                'nombre': c.nombreCuenta,
                'debe': c.debe,
                'haber': c.haber,
                'saldo': c.saldo_calculado,
                'tipo_saldo': c.tipo_saldo_calculado,
            })
        return filas

    activos_data = procesar_cuentas(activos)
    pasivos_data = procesar_cuentas(pasivos)
    
    total_activos = sum(c['saldo'] for c in activos_data)
    total_pasivos = sum(c['saldo'] for c in pasivos_data) 
    
    total_patrimonio = capital_final
    tipo_saldo_capital = 'Acreedor' if capital_final >= 0 else 'Deudor'

    diferencia_balance = total_activos - (total_pasivos + total_patrimonio)

    # Fechas y contexto
    fecha_inicio_str = fecha_inicio.strftime("%d de %B de %Y").capitalize()
    fecha_fin_str = fecha_fin.strftime("%d de %B de %Y").capitalize()

    contexto = {
        "periodos": periodos_disponibles,
        "periodo_seleccionado": periodo_activo,
        "sin_periodo": False, 
        
        # Estado de Resultados
        "ingresos": ingresos,
        "gastos": gastos,
        "total_ingresos": total_ingresos,
        "total_gastos": total_gastos,
        "utilidad_bruta": utilidad_bruta,
        "impuesto": impuesto, 
        "utilidad_neta": utilidad_neta, 

        # Estado de Capital
        "capital_inicial": capital_inicial, # Saldo inicial del periodo (0 para #1)
        "capital_social": capital_social, # Saldo de la 3101 al cierre (antes de utilidad)
        "capital_final": capital_final, # Saldo final para Balance General
        
        # Balance General
        "activos": activos_data,
        "pasivos": pasivos_data,
        "total_activos": total_activos,
        "total_pasivos": total_pasivos,
        "total_patrimonio": total_patrimonio,
        "tipo_saldo_capital": tipo_saldo_capital,
        "diferencia_balance": diferencia_balance,
        
        # Fechas
        "fecha_inicio": fecha_inicio_str,
        "fecha_fin": fecha_fin_str,
        "fecha_hoy": date.today().strftime("%d de %B de %Y").capitalize(),
    }

    return render(request, "estados.html", contexto)