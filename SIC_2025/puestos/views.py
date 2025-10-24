from django.shortcuts import render, redirect
from .models import Puesto

def registrar_puesto(request):
    # Datos fijos
    dias_vacaciones = 15
    recargo_vacaciones = 0.30
    dias_aguinaldo = 18
    seguro_social = 0.075
    afp = 0.0875

    # Valores iniciales
    nombre = ""
    salario_nominal = ""
    eficiencia = ""

    contexto = {
        "resultado": None,
        "puestos": Puesto.objects.all(),
        "dias_vacaciones": dias_vacaciones,
        "recargo_vacaciones": recargo_vacaciones,
        "dias_aguinaldo": dias_aguinaldo,
        "nombre": nombre,
        "salario": salario_nominal,
        "eficiencia": eficiencia,
    }

    if request.method == "POST":
        nombre = request.POST.get("nombre", "")
        salario_nominal = request.POST.get("salario", "")
        eficiencia = request.POST.get("eficiencia", "")

        # Guardamos los valores en el contexto para no perderlos
        contexto["nombre"] = nombre
        contexto["salario"] = salario_nominal
        contexto["eficiencia"] = eficiencia

        if salario_nominal and eficiencia:
            salario_nominal = float(salario_nominal)
            eficiencia = float(eficiencia)

            # ---- Cálculos ----
            costo_semanal = salario_nominal * 5
            septimo = salario_nominal * 2
            vacaciones_semanales = ((salario_nominal * dias_vacaciones) * (1 + recargo_vacaciones + seguro_social + afp)) / 52
            aguinaldo_semanal = (salario_nominal * dias_aguinaldo) / 52
            salario_cancelado = costo_semanal + septimo + vacaciones_semanales
            isss = salario_cancelado * seguro_social
            afp_valor = salario_cancelado * afp
            costo_real_semana = salario_cancelado + aguinaldo_semanal + isss + afp_valor
            costo_real_dia = costo_real_semana / 5
            costo_real_dia_eficiencia = costo_real_dia / eficiencia
            costo_real_mes_eficiencia = costo_real_dia_eficiencia * 20
            costo_real_hora = costo_real_dia / 8
            costo_real_hora_eficiencia = costo_real_dia_eficiencia / 8

            # Resultado a mostrar
            resultado = {
                "Salario nominal": salario_nominal,
                "Costo por semana laboral": costo_semanal,
                "Séptimo (dos días)": septimo,
                "Vacaciones semanales": round(vacaciones_semanales, 2),
                "Aguinaldo semanal": round(aguinaldo_semanal, 2),
                "Cálculo de salario cancelado": round(salario_cancelado, 2),
                "ISSS": round(isss, 2),
                "AFP": round(afp_valor, 2),
                "Costo real de mano de obra semanal": round(costo_real_semana, 2),
                "Costo real de mano de obra diaria": round(costo_real_dia, 2),
                "Costo real de mano de obra al día con eficiencia": round(costo_real_dia_eficiencia, 2),
                "Costo real de mano de obra al MES con eficiencia": round(costo_real_mes_eficiencia, 2),
                "Costo real de mano de obra por hora": round(costo_real_hora, 2),
                "Costo real de mano de obra por hora con eficiencia": round(costo_real_hora_eficiencia, 2),
            }

            # Si se presiona "Registrar Puesto"
            if "registrar" in request.POST:
                Puesto.objects.create(
                    nombrePuesto=nombre,
                    salarioHoraPuesto=costo_real_hora_eficiencia,
                    salarioDiarioPuesto=costo_real_dia_eficiencia,
                    salarioMesPuesto=costo_real_mes_eficiencia,
                )
                return redirect("registrar_puesto")

            contexto["resultado"] = resultado

    return render(request, "registrar_puesto.html", contexto)

