from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import PeriodoContable
from .forms import PeriodoContableForm
from cuentas.models import Cuenta
from  decimal import Decimal

# ------------------- LISTA DE PERIODOS -------------------

def lista_periodos(request):
    periodos = PeriodoContable.objects.all()
    return render(request, "lista_periodos.html", {"periodos": periodos})


# ------------------- CREAR NUEVO PERIODO -------------------

def crear_periodo(request):
    if request.method == "POST":
        form = PeriodoContableForm(request.POST)
        if form.is_valid():
            #Verificar si hay un periodo activo
            if PeriodoContable.objects.filter(activo=True).exists():
                messages.error(
                    request,
                    "Ya existe un periodo activo. Cierre el periodo actual antes de crear uno nuevo."
                )
                return redirect('lista_periodos')

            #Guardar el nuevo periodo
            nuevo_periodo = form.save(commit=False)
            nuevo_periodo.activo = True
            nuevo_periodo.save()

            # Trasladar saldos del periodo anterior (si existe)
            periodo_anterior = PeriodoContable.objects.filter(
                fecha_fin__lt=nuevo_periodo.fecha_inicio
            ).order_by('-fecha_fin').first()

            if periodo_anterior:
                for cuenta in Cuenta.objects.all():
                    tipo = cuenta.subTipoCuenta.tipoCuenta.codTipoCuenta[0]
                    saldo = cuenta.saldo_final or Decimal('0.00')

                    # Activos → saldo deudor
                    if tipo == '1':
                        cuenta.debe = saldo if saldo > 0 else Decimal('0.00')
                        cuenta.haber = abs(saldo) if saldo < 0 else Decimal('0.00')

                    # Pasivos y Capital → saldo acreedor
                    elif tipo in ['2', '3']:
                        cuenta.haber = saldo if saldo > 0 else Decimal('0.00')
                        cuenta.debe = abs(saldo) if saldo < 0 else Decimal('0.00')

                    # Ingresos y Gastos → reiniciar a cero
                    elif tipo in ['4', '5']:
                        cuenta.debe = Decimal('0.00')
                        cuenta.haber = Decimal('0.00')

                    cuenta.save()

            messages.success(
                request,
                "Periodo creado correctamente con saldos iniciales trasladados."
            )
            return redirect('lista_periodos')

    else:
        form = PeriodoContableForm()

    return render(request, 'crear_periodo.html', {'form': form})


# ------------------- CERRAR PERIODO -------------------

def cerrar_periodo(request, pk):
    periodo = get_object_or_404(PeriodoContable, pk=pk)
    try:
        # Método del modelo ya calcula saldos finales según naturaleza contable
        periodo.cerrar_periodo()
        messages.success(request, "Periodo cerrado correctamente y saldos finales calculados.")
    except Exception as e:
        messages.error(request, "Error al cerrar el periodo: " + str(e))
    return redirect("lista_periodos")