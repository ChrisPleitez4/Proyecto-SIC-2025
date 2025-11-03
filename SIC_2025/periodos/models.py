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

    def cerrar_periodo(self):
        """Cierra el periodo solo si la fecha actual >= fecha_fin"""
        if timezone.now().date() < self.fecha_fin:
            raise ValueError("No se puede cerrar el periodo antes de su fecha de fin.")
        self.activo = False
        self.fecha_cierre = timezone.now()
        self.save()
    
    def guardar(self, *args, **kwargs):
        """Evita periodos que solapen otro activo"""
        if self.activo:
            super_periodos = PeriodoContable.objects.filter(activo=True).exclude(id=self.id)
            for p in super_periodos:
                if (self.fecha_inicio <= p.fecha_fin and self.fecha_fin >= p.fecha_inicio):
                    raise ValueError("No puede haber periodos activos que se solapen.")
        if self.fecha_inicio > self.fecha_fin:
            raise ValueError("La fecha de inicio no puede ser mayor a la fecha de fin.")
        super().save(*args, **kwargs)

class SaldoCuenta(models.Model):
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoContable, on_delete=models.CASCADE)
    saldo_final = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        unique_together = ('cuenta', 'periodo')

    def __str__(self):
        return f"{self.cuenta.nombreCuenta} - {self.periodo.nombre}: {self.saldo_final}"

    @classmethod
    def calcular_saldos_periodo(cls, periodo):
        cuentas = Cuenta.objects.all()
        
        # Calcular utilidad neta del periodo (Ingresos - Gastos)
        ingresos = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='5')
        gastos   = cuentas.filter(subTipoCuenta__tipoCuenta__codTipoCuenta__startswith='4')
        total_ingresos = sum(((c.haber - c.debe) for c in ingresos), 0)
        total_gastos   = sum(((c.debe - c.haber) for c in gastos), 0)
        utilidad_neta  = total_ingresos - total_gastos

        for cuenta in cuentas:
            movimientos = cuenta.movimientos.filter(transaccion__periodo=periodo)
            
            # Reglas específicas
            if cuenta.codCuenta == '3101':  
                # Capital Social = movimientos + utilidad neta del periodo
                saldo_final = sum([m.monto if not m.tipo else -m.monto for m in movimientos]) + utilidad_neta
            
            elif cuenta.subTipoCuenta.tipoCuenta.codTipoCuenta.startswith(('4', '5')):
                # Cuentas de gastos e ingresos se reinician a 0
                saldo_final = Decimal('0.00')
            
            else:
                # Otras cuentas (activos, pasivos, etc.)
                saldo_final = sum([m.monto if m.tipo else -m.monto for m in movimientos])
            
            # Crear o actualizar registro
            cls.objects.update_or_create(
                cuenta=cuenta,
                periodo=periodo,
                defaults={'saldo_final': saldo_final}
            )
