from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
from .models import PeriodoContable, SaldoCuenta
from .forms import PeriodoContableForm
from cuentas.models import Cuenta


# ------------------- PERIODO CONTABLE -------------------

def lista_periodos(request):
    periodos = PeriodoContable.objects.all()
    return render(request, "lista_periodos.html", {"periodos": periodos})


def crear_periodo(request):
    if request.method == "POST":
        form = PeriodoContableForm(request.POST)
        if form.is_valid():
            # Verificar si hay un periodo activo
            if PeriodoContable.objects.filter(activo=True).exists():
                messages.error(request, "Ya existe un periodo activo. Cierre el periodo actual antes de crear uno nuevo.")
                return redirect('lista_periodos')

            # Guardar periodo como activo
            nuevo_periodo = form.save(commit=False)
            nuevo_periodo.activo = True
            nuevo_periodo.save()

            # Inicializar saldos del nuevo periodo con saldos finales del periodo anterior
            inicializar_saldos_nuevo_periodo(nuevo_periodo)

            messages.success(request, "Periodo creado correctamente.")
            return redirect('lista_periodos')
    else:
        form = PeriodoContableForm()
    return render(request, 'crear_periodo.html', {'form': form})


def cerrar_periodo(request, pk):
    periodo = get_object_or_404(PeriodoContable, pk=pk)
    try:
        periodo.cerrar_periodo()
        # Calcular saldos finales al cerrar el periodo y trasladar utilidad
        SaldoCuenta.calcular_saldos_periodo(periodo)
        messages.success(request, "Periodo cerrado correctamente y saldos calculados.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("lista_periodos")


# ------------------- FUNCIONES AUXILIARES -------------------

def inicializar_saldos_nuevo_periodo(periodo):
    """Inicializa los saldos del nuevo periodo tomando el saldo final del periodo anterior"""
    cuentas = Cuenta.objects.all()
    periodo_anterior = PeriodoContable.objects.filter(fecha_fin__lt=periodo.fecha_inicio).order_by('-fecha_fin').first()

    for cuenta in cuentas:
        saldo_inicial = Decimal('0.00')
        if periodo_anterior:
            saldo_anterior_obj = SaldoCuenta.objects.filter(
                cuenta=cuenta,
                periodo=periodo_anterior
            ).first()
            if saldo_anterior_obj:
                saldo_inicial = saldo_anterior_obj.saldo_final

        # Crear el saldo inicial en el nuevo periodo
        SaldoCuenta.objects.update_or_create(
            cuenta=cuenta,
            periodo=periodo,
            defaults={'saldo_final': saldo_inicial}
        )