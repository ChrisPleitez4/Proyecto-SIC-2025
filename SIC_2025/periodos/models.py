from django.db import models
from django.utils import timezone
from cuentas.models import Cuenta
from decimal import Decimal


class PeriodoContable(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_inicio']

    def __str__(self):
        estado = "Activo" if self.activo else "Cerrado"
        return f"{self.nombre} ({estado})"

    # -----------------------------------------
    # 🔒 CIERRE DEL PERIODO CONTABLE
    # -----------------------------------------
    def cerrar_periodo(self):

        from transacciones.models import Movimiento, Transaccion

        hoy = timezone.localdate()

        #Validar que no existan transacciones posteriores a hoy
        trans_posteriores = Movimiento.objects.filter(transaccion__fecha__gt=hoy)
        if trans_posteriores.exists():
            raise ValueError(
                "Existen transacciones con fecha posterior a hoy."
            )


        cuentas = Cuenta.objects.all()

        # calcular utilidad neta solo de este periodo
        ingresos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='5')
        gastos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='4')
        total_ingresos = sum((c.haber - c.debe) for c in ingresos)
        total_gastos = sum((c.debe - c.haber) for c in gastos)
        utilidad_neta = total_ingresos - total_gastos

        for cuenta in cuentas:
            tipo = cuenta.subTipoCuenta.tipoCuenta.codTipoCuenta[0]

            if tipo in ['4', '5']:
                saldo = Decimal('0.00')
                cuenta.debe = Decimal('0.00')
                cuenta.haber = Decimal('0.00')
            elif tipo == '1':
                saldo = cuenta.debe - cuenta.haber
            elif tipo in ['2', '3']:
                saldo = cuenta.haber - cuenta.debe

            if cuenta.codCuenta == '3101':
                saldo += utilidad_neta

            cuenta.saldo_final = saldo
            cuenta.save()

        self.activo = False
        self.fecha_cierre = timezone.now()
        self.fecha_fin = self.fecha_cierre
        if self.fecha_inicio > hoy:
            raise ValueError(
                "No puede cerrarse antes de la fecha de inicio."
            )
        self.save()

    # -----------------------------------------
    # 🚀 APERTURA DE NUEVO PERIODO
    # -----------------------------------------
def abrir_nuevo_periodo(self, nombre, fecha_inicio, fecha_fin):
    """Abre un nuevo periodo trasladando saldos iniciales según la naturaleza de la cuenta."""
    nuevo_periodo = PeriodoContable.objects.create(
        nombre=nombre,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        activo=True
    )

    for cuenta in Cuenta.objects.all():
        cuenta.debe = Decimal('0.00')
        cuenta.haber = Decimal('0.00')

        tipo = cuenta.subTipoCuenta.tipoCuenta.codTipoCuenta[0]
        saldo = cuenta.saldo_final or Decimal('0.00')

        # Solo trasladar activos, pasivos y capital
        if tipo in ['1', '2', '3']:
            if tipo == '1':  # Activo → saldo deudor
                if saldo > 0:
                    cuenta.debe = saldo
                elif saldo < 0:
                    cuenta.haber = abs(saldo)

            elif tipo in ['2', '3']:  # Pasivo o Capital → saldo acreedor
                if saldo > 0:
                    cuenta.haber = saldo
                elif saldo < 0:
                    cuenta.debe = abs(saldo)

        cuenta.save()

    return nuevo_periodo
