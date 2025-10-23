from django.db import migrations

def crear_datos_iniciales(apps, schema_editor):
    TipoCuenta = apps.get_model('cuentas', 'TipoCuenta')
    SubTipoCuenta = apps.get_model('cuentas', 'SubTipoCuenta')
    Cuenta = apps.get_model('cuentas', 'Cuenta')

    # --- ACTIVO ---
    activo = TipoCuenta.objects.create(codTipoCuenta='1', nombreRubro='ACTIVO')

    act_corriente = SubTipoCuenta.objects.create(codSubTipoCuenta='11', nombreSubCuenta='Activo corriente', tipoCuenta=activo)
    Cuenta.objects.bulk_create([
        Cuenta(codCuenta='1101', nombreCuenta='Caja', subTipoCuenta=act_corriente),
        Cuenta(codCuenta='1102', nombreCuenta='Bancos', subTipoCuenta=act_corriente),
        Cuenta(codCuenta='1103', nombreCuenta='Cuentas por cobrar clientes', subTipoCuenta=act_corriente),
        Cuenta(codCuenta='1104', nombreCuenta='IVA crédito fiscal', subTipoCuenta=act_corriente),
        Cuenta(codCuenta='1105', nombreCuenta='Anticipos a proveedores', subTipoCuenta=act_corriente),
    ])

    act_nocorriente = SubTipoCuenta.objects.create(codSubTipoCuenta='12', nombreSubCuenta='Activo no corriente', tipoCuenta=activo)
    Cuenta.objects.bulk_create([
        Cuenta(codCuenta='1201', nombreCuenta='Gastos pagados por anticipado', subTipoCuenta=act_nocorriente),
        Cuenta(codCuenta='1202', nombreCuenta='Equipo de cómputo y mobiliario', subTipoCuenta=act_nocorriente),
        Cuenta(codCuenta='1203', nombreCuenta='Depreciación acumulada', subTipoCuenta=act_nocorriente),
    ])

    # --- PASIVO ---
    pasivo = TipoCuenta.objects.create(codTipoCuenta='2', nombreRubro='PASIVO')

    pas_corriente = SubTipoCuenta.objects.create(codSubTipoCuenta='21', nombreSubCuenta='Pasivo corriente', tipoCuenta=pasivo)
    Cuenta.objects.bulk_create([
        Cuenta(codCuenta='2101', nombreCuenta='Cuentas por pagar', subTipoCuenta=pas_corriente),
        Cuenta(codCuenta='2102', nombreCuenta='Anticipo de clientes', subTipoCuenta=pas_corriente),
        Cuenta(codCuenta='2103', nombreCuenta='Retenciones por pagar (Débito Fiscal)', subTipoCuenta=pas_corriente),
    ])

    pas_nocorriente = SubTipoCuenta.objects.create(codSubTipoCuenta='22', nombreSubCuenta='Pasivo no corriente', tipoCuenta=pasivo)
    Cuenta.objects.bulk_create([
        Cuenta(codCuenta='2201', nombreCuenta='Documentos por pagar', subTipoCuenta=pas_nocorriente),
    ])

    # --- CAPITAL ---
    capital = TipoCuenta.objects.create(codTipoCuenta='3', nombreRubro='CAPITAL')

    patrimonio = SubTipoCuenta.objects.create(codSubTipoCuenta='31', nombreSubCuenta='Patrimonio', tipoCuenta=capital)
    Cuenta.objects.bulk_create([
        Cuenta(codCuenta='3101', nombreCuenta='Capital social', subTipoCuenta=patrimonio),
        Cuenta(codCuenta='3102', nombreCuenta='Pérdidas y ganancias', subTipoCuenta=patrimonio),
    ])

    # --- GASTOS ---
    gastos = TipoCuenta.objects.create(codTipoCuenta='4', nombreRubro='GASTOS')

    gastos_admin = SubTipoCuenta.objects.create(codSubTipoCuenta='41', nombreSubCuenta='Gastos administrativos', tipoCuenta=gastos)
    Cuenta.objects.bulk_create([
        Cuenta(codCuenta='4101', nombreCuenta='Sueldos administrativos', subTipoCuenta=gastos_admin),
        Cuenta(codCuenta='4102', nombreCuenta='Servicios básicos', subTipoCuenta=gastos_admin),
        Cuenta(codCuenta='4103', nombreCuenta='Alquiler de oficina', subTipoCuenta=gastos_admin),
        Cuenta(codCuenta='4104', nombreCuenta='Papelería y suministros', subTipoCuenta=gastos_admin),
        Cuenta(codCuenta='4105', nombreCuenta='Depreciación de equipos de cómputo', subTipoCuenta=gastos_admin),
        Cuenta(codCuenta='4106', nombreCuenta='Gastos de representación y marketing', subTipoCuenta=gastos_admin),
    ])

    gastos_oper = SubTipoCuenta.objects.create(codSubTipoCuenta='42', nombreSubCuenta='Gastos operativos', tipoCuenta=gastos)
    Cuenta.objects.bulk_create([
        Cuenta(codCuenta='4201', nombreCuenta='Sueldos técnicos y desarrolladores', subTipoCuenta=gastos_oper),
        Cuenta(codCuenta='4202', nombreCuenta='Licencias y software utilizados en proyectos', subTipoCuenta=gastos_oper),
        Cuenta(codCuenta='4203', nombreCuenta='Hosting y dominios', subTipoCuenta=gastos_oper),
        Cuenta(codCuenta='4204', nombreCuenta='Mantenimiento de equipos informáticos', subTipoCuenta=gastos_oper),
        Cuenta(codCuenta='4205', nombreCuenta='Capacitación técnica', subTipoCuenta=gastos_oper),
    ])

    # --- INGRESOS ---
    ingresos = TipoCuenta.objects.create(codTipoCuenta='5', nombreRubro='INGRESOS')

    ingresos_serv = SubTipoCuenta.objects.create(codSubTipoCuenta='51', nombreSubCuenta='Ingresos por servicios', tipoCuenta=ingresos)
    Cuenta.objects.bulk_create([
        Cuenta(codCuenta='5101', nombreCuenta='Desarrollo de software a la medida', subTipoCuenta=ingresos_serv),
        Cuenta(codCuenta='5102', nombreCuenta='Asesorías tecnológicas', subTipoCuenta=ingresos_serv),
        Cuenta(codCuenta='5103', nombreCuenta='Mantenimiento y soporte técnico', subTipoCuenta=ingresos_serv),
    ])

class Migration(migrations.Migration):

    dependencies = [
        ('cuentas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_datos_iniciales),
    ]
