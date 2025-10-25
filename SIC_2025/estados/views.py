from django.shortcuts import render
from cuentas.models import Cuenta
from decimal import Decimal
from datetime import date

def estados_financieros(request):
    cuentas = Cuenta.objects.select_related('subTipoCuenta__tipoCuenta')

    # ===== Estado de Resultados =====
    ingresos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='5')
    gastos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='4')

    total_ingresos = sum((c.haber - c.debe) for c in ingresos)
    total_gastos = sum((c.debe - c.haber) for c in gastos)
    utilidad_bruta = total_ingresos - total_gastos
    impuesto = utilidad_bruta * Decimal('0.13')
    utilidad_neta = utilidad_bruta - impuesto

    # ===== Estado de Capital =====
    capital_social_cuenta = cuentas.filter(nombreCuenta__icontains='capital social').first()
    capital_inicial = (capital_social_cuenta.haber - capital_social_cuenta.debe) if capital_social_cuenta else Decimal('0.00')
    capital_final = capital_inicial + utilidad_neta

    # ===== Balance General =====
    activos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='1')
    pasivos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='2')
    patrimonio = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='3').exclude(nombreCuenta__icontains='pérdidas y ganancias')

    contexto = {
        'fecha': date.today(),
        'ingresos': ingresos,
        'gastos': gastos,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'utilidad_bruta': utilidad_bruta,
        'impuesto': impuesto,
        'utilidad_neta': utilidad_neta,
        'capital_inicial': capital_inicial,
        'capital_final': capital_final,
        'activos': activos,
        'pasivos': pasivos,
        'patrimonio': patrimonio,
    }

    return render(request, 'estados.html', contexto)
