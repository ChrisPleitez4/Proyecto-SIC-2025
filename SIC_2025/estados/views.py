from django.shortcuts import render
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


# ---------------------------------------------------------------------
# 🌐 View: Estados Financieros
# ---------------------------------------------------------------------
def estados_financieros(request):
    periodo_activo = PeriodoContable.objects.filter(activo=True).first()
    if not periodo_activo:
        messages.error(request, "No hay un periodo contable activo. Cierre o active uno antes de continuar.")
        return render(request, "estados.html", {"sin_periodo": True})

    fecha_inicio = periodo_activo.fecha_inicio
    fecha_fin = periodo_activo.fecha_fin

    cuentas = Cuenta.objects.select_related('subTipoCuenta__tipoCuenta').all()

    # -----------------------------
    # 🔹 Calcular debe/haber con saldo inicial + movimientos del periodo
    # -----------------------------
    for cuenta in cuentas:
        tipo = cuenta.subTipoCuenta.tipoCuenta.codTipoCuenta[0]

        # Saldo inicial viene del saldo_final del periodo anterior
        saldo_inicial = cuenta.saldo_final or Decimal('0.00')
        cuenta.debe = Decimal('0.00')
        cuenta.haber = Decimal('0.00')

        # ✅ Cargar saldo inicial correctamente según naturaleza
        if tipo == '1':  # Activo → saldo deudor
            if saldo_inicial > 0:
                cuenta.debe = saldo_inicial
            elif saldo_inicial < 0:
                cuenta.haber = abs(saldo_inicial)
        elif tipo in ['2', '3']:  # Pasivo o Capital → saldo acreedor
            if saldo_inicial > 0:
                cuenta.haber = saldo_inicial
            elif saldo_inicial < 0:
                cuenta.debe = abs(saldo_inicial)
        # Gastos e ingresos (4 y 5) no trasladan saldo

        # 🔁 Sumar movimientos del periodo activo
        movimientos = Movimiento.objects.filter(
            cuenta=cuenta,
            transaccion__fecha__range=[fecha_inicio, fecha_fin]
        )

        cuenta.debe += sum(m.monto for m in movimientos if m.tipo) or Decimal('0.00')
        cuenta.haber += sum(m.monto for m in movimientos if not m.tipo) or Decimal('0.00')

    # -----------------------------
    # 🧾 Estado de Resultados
    # -----------------------------
    ingresos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='5')
    gastos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='4')

    total_ingresos = sum(c.saldo_cuenta() for c in ingresos)
    total_gastos = sum(c.saldo_cuenta() for c in gastos)

    utilidad_bruta = total_ingresos - total_gastos

    # 🚫 SIN IMPUESTO NI UTILIDAD NETA
    impuesto = Decimal('0.00')          # Se mantiene en contexto por compatibilidad
    utilidad_neta = utilidad_bruta      # Alias para no romper plantillas existentes

    # -----------------------------
    # 💰 Estado de Capital
    # -----------------------------
    capital_cuenta = cuentas.filter(codCuenta='3101').first()  # 3101 = Capital Social
    capital_social = Decimal('0.00')
    capital_inicial = Decimal('0.00')
    capital_movimientos = Decimal('0.00')

    if capital_cuenta:
        tipo = capital_cuenta.subTipoCuenta.tipoCuenta.codTipoCuenta[0]
        # saldo inicial
        saldo_inicial = capital_cuenta.saldo_final or Decimal('0.00')
        if tipo in ['2', '3']:  # Capital → saldo acreedor
            capital_inicial = saldo_inicial
        # movimientos del periodo (acreedor - deudor)
        movimientos = Movimiento.objects.filter(
            cuenta=capital_cuenta,
            transaccion__fecha__range=[fecha_inicio, fecha_fin]
        )
        capital_movimientos = sum(m.monto for m in movimientos if not m.tipo) - sum(m.monto for m in movimientos if m.tipo)

    capital_social = (capital_inicial + capital_movimientos).quantize(Decimal('0.01'))
    # Capital final suma utilidad BRUTA (ya no hay impuesto)
    capital_final = (capital_inicial + capital_movimientos + utilidad_bruta).quantize(Decimal('0.01'))

    # -----------------------------
    # 📊 Balance General
    # -----------------------------
    activos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='1')
    pasivos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='2')
    capital = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='3')

    def procesar_cuentas(qs):
        filas = []
        for c in qs:
            filas.append({
                'cod': c.codCuenta,
                'nombre': c.nombreCuenta,
                'debe': c.debe,
                'haber': c.haber,
                'saldo': c.saldo_cuenta(),
                'tipo_saldo': c.tipo_saldo(),
            })
        return filas

    activos_data = procesar_cuentas(activos)
    pasivos_data = procesar_cuentas(pasivos)
    capital_data = procesar_cuentas(capital)

    total_activos = sum(c['saldo'] for c in activos_data)
    total_pasivos = sum(c['saldo'] for c in pasivos_data)
    # En el balance presentas un solo Capital = capital_final
    total_patrimonio = capital_final
    tipo_saldo_capital = 'Acreedor' if capital_final >= 0 else 'Deudor'

    diferencia_balance = total_activos - (total_pasivos + total_patrimonio)

    # -----------------------------
    # 🕓 Fechas y contexto
    # -----------------------------
    fecha_inicio_str = fecha_inicio.strftime("%d de %B de %Y").capitalize()
    fecha_fin_str = fecha_fin.strftime("%d de %B de %Y").capitalize()

    contexto = {
        "ingresos": ingresos,
        "gastos": gastos,
        "total_ingresos": total_ingresos,
        "total_gastos": total_gastos,
        "utilidad_bruta": utilidad_bruta,

        # Quedan en contexto por compatibilidad, pero no afectan nada
        "impuesto": impuesto,              # = 0.00
        "utilidad_neta": utilidad_neta,    # = utilidad_bruta

        "capital_inicial": capital_inicial,
        "capital_social": capital_social,
        "capital_final": capital_final,

        "activos": activos_data,
        "pasivos": pasivos_data,
        "capital": capital_data,

        "total_activos": total_activos,
        "total_pasivos": total_pasivos,
        "total_patrimonio": total_patrimonio,
        "tipo_saldo_capital": tipo_saldo_capital,

        "diferencia_balance": diferencia_balance,
        "fecha_inicio": fecha_inicio_str,
        "fecha_fin": fecha_fin_str,
        "fecha_hoy": fecha_fin.strftime("%d de %B de %Y").capitalize(),
    }

    return render(request, "estados.html", contexto)
