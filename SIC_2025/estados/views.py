from django.shortcuts import render
from cuentas.models import Cuenta
from decimal import Decimal, getcontext
from datetime import date, timedelta
import locale

# Locale español para nombres de meses
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        # Fallback común en Windows
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain')
    except:
        pass

getcontext().prec = 18

def estados_financieros(request):
    cuentas = Cuenta.objects.select_related('subTipoCuenta__tipoCuenta')

    # ===== ESTADO DE RESULTADOS =====
    ingresos_qs = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='5')
    gastos_qs   = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='4')

    # OJO: generadores entre paréntesis porque usamos segundo argumento de sum()
    total_ingresos = sum(((c.haber - c.debe) for c in ingresos_qs), Decimal('0.00'))
    total_gastos   = sum(((c.debe  - c.haber) for c in gastos_qs),   Decimal('0.00'))

    utilidad_bruta = total_ingresos - total_gastos
    impuesto       = (utilidad_bruta * Decimal('0.13')).quantize(Decimal('0.01'))
    utilidad_neta  = (utilidad_bruta - impuesto).quantize(Decimal('0.01'))

    # Fechas del periodo (últimos 12 meses)
    fecha_fin    = date.today()
    fecha_inicio = fecha_fin - timedelta(days=365) + timedelta(days=1)
    fecha_inicio_str = fecha_inicio.strftime("%d de %B de %Y").capitalize()
    fecha_fin_str    = fecha_fin.strftime("%d de %B de %Y").capitalize()

    # ===== ESTADO DE CAPITAL =====
    # Capital Social = 3101 (saldo: Haber - Debe)
    cap_soc = cuentas.filter(codCuenta='3101').first()
    capital_inicial = (cap_soc.haber - cap_soc.debe).quantize(Decimal('0.01')) if cap_soc else Decimal('0.00')
    capital_final   = (capital_inicial + utilidad_neta).quantize(Decimal('0.01'))

    # ===== BALANCE GENERAL =====
    activos_qs = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='1')
    pasivos_qs = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='2')

    def procesar_cuentas(qs, tipo):
        filas = []
        for c in qs:
            if tipo == 'activo':
                saldo = (c.debe - c.haber) or Decimal('0.00')
            else:  # pasivo
                saldo = (c.haber - c.debe) or Decimal('0.00')
            filas.append({
                'cod': c.codCuenta,
                'nombre': c.nombreCuenta,
                'debe': c.debe,
                'haber': c.haber,
                'saldo': saldo,
                'tipo_saldo': c.tipo_saldo(),
            })
        return filas

    activos = procesar_cuentas(activos_qs, 'activo')
    pasivos = procesar_cuentas(pasivos_qs, 'pasivo')

    # También aquí: generadores entre paréntesis
    total_activos = sum((a['saldo'] for a in activos), Decimal('0.00'))
    total_pasivos = sum((p['saldo'] for p in pasivos), Decimal('0.00'))

    # Patrimonio del Balance = capital final (capital social + utilidad neta ya operada)
    total_patrimonio = capital_final

    diferencia_balance = total_activos - (total_pasivos + total_patrimonio)

    # Tipo de saldo para la fila única de patrimonio
    if total_patrimonio > 0:
        capital_tipo_saldo = "Acreedor"
    elif total_patrimonio < 0:
        capital_tipo_saldo = "Deudor"
    else:
        capital_tipo_saldo = "Saldo Cero"

    contexto = {
        # Estado de Resultados
        'ingresos': ingresos_qs,
        'gastos': gastos_qs,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'utilidad_bruta': utilidad_bruta,
        'impuesto': impuesto,
        'utilidad_neta': utilidad_neta,
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,

        # Estado de Capital
        'capital_inicial': capital_inicial,
        'capital_final': capital_final,

        # Balance General
        'activos': activos,
        'pasivos': pasivos,
        'total_activos': total_activos,
        'total_pasivos': total_pasivos,
        'total_patrimonio': total_patrimonio,  # = capital_final
        'capital_tipo_saldo': capital_tipo_saldo,
        'diferencia_balance': diferencia_balance,

        # Fecha actual
        'fecha_hoy': fecha_fin.strftime("%d de %B de %Y").capitalize(),
    }
    return render(request, 'estados.html', contexto)
