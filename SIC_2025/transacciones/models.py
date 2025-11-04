from django.db import models
from cuentas.models import Cuenta
from periodos.models import PeriodoContable

# Create your models here
class Transaccion(models.Model):
    descripcion = models.CharField(max_length=150)
    nro_transaccion = models.PositiveIntegerField()
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    periodo = models.ForeignKey(
        PeriodoContable,
        on_delete=models.PROTECT,  # no permite borrar un periodo si tiene transacciones
        related_name='transacciones',
        null=True,  # se asignará automáticamente al periodo activo
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.periodo:
            # asigna el periodo activo automáticamente
            self.periodo = PeriodoContable.objects.get(activo=True)
        
        if not self.pk:  # Solo al crear, no al actualizar
            ultimo = Transaccion.objects.filter(periodo=self.periodo).order_by('-nro_transaccion').first()
            if ultimo:
                self.nro_transaccion = ultimo.nro_transaccion + 1
            else:
                self.nro_transaccion = 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Transacción {self.nro_transaccion} ({self.periodo.nombre}) - {self.descripcion}"
    

        
class Movimiento(models.Model):
    DEUDORA=True
    ACREEDORA=False
    TIPO_CHOICES=[  
        (DEUDORA,'Deudora'),
        (ACREEDORA,'Acreedora')
    ]
    
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    tipo = models.BooleanField(choices=TIPO_CHOICES)  # True=deudora, False=acreedora
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name='movimientos')
    transaccion =models.ForeignKey(Transaccion, on_delete=models.CASCADE,related_name='movimientos')
    
    
    def __str__(self):
        tipo_str = "Debe" if self.tipo else "Haber"
        return f"{tipo_str} - {self.importe} - {self.descripcion}"
    