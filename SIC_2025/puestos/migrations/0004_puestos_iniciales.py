from django.db import migrations

def crear_puestos_iniciales(apps, schema_editor):
    Puesto = apps.get_model('puestos', 'Puesto')

    puestos = [
        {
            "idPuesto": 1,
            "nombrePuesto": "Gerente general",
            "salarioHoraPuesto": 18.39,
            "salarioDiarioPuesto": 147.09,
            "salarioMesPuesto": 2941.80,
            "administrativo": True,
        },
        {
            "idPuesto": 2,
            "nombrePuesto": "Asistente contable",
            "salarioHoraPuesto": 8.49,
            "salarioDiarioPuesto": 67.89,
            "salarioMesPuesto": 1357.75,
            "administrativo": True,
        },
        {
            "idPuesto": 3,
            "nombrePuesto": "Jefe de proyectos",
            "salarioHoraPuesto": 12.73,
            "salarioDiarioPuesto": 101.83,
            "salarioMesPuesto": 2036.63,
            "administrativo": False,
        },
        {
            "idPuesto": 4,
            "nombrePuesto": "Desarrollador de software",
            "salarioHoraPuesto": 10.61,
            "salarioDiarioPuesto": 84.86,
            "salarioMesPuesto": 1697.19,
            "administrativo": False,
        },
        {
            "idPuesto": 5,
            "nombrePuesto": "Consultor tecnologico",
            "salarioHoraPuesto": 12.02,
            "salarioDiarioPuesto": 96.17,
            "salarioMesPuesto": 1923.48,
            "administrativo": False,
        },
        {
            "idPuesto": 6,
            "nombrePuesto": "Tenico de soporte",
            "salarioHoraPuesto": 7.07,
            "salarioDiarioPuesto": 56.57,
            "salarioMesPuesto": 1131.46,
            "administrativo": False,
        },
        {
            "idPuesto": 7,
            "nombrePuesto": "QA Tester",
            "salarioHoraPuesto": 9.90,
            "salarioDiarioPuesto": 79.20,
            "salarioMesPuesto": 1584.04,
            "administrativo": False,
        },
        {
            "idPuesto": 8,
            "nombrePuesto": "Ejecutivo de ventas",
            "salarioHoraPuesto": 9.19,
            "salarioDiarioPuesto": 73.54,
            "salarioMesPuesto": 1470.90,
            "administrativo": True,
        },
        {
            "idPuesto": 9,
            "nombrePuesto": "Marketing",
            "salarioHoraPuesto": 8.49,
            "salarioDiarioPuesto": 67.89,
            "salarioMesPuesto": 1357.75,
            "administrativo": True,
        },
    ]

    for p in puestos:
        Puesto.objects.create(**p)

class Migration(migrations.Migration):

    dependencies = [
        ('puestos', '0005_alter_puesto_nombrepuesto'),  
    ]

    operations = [
        migrations.RunPython(crear_puestos_iniciales),
    ]