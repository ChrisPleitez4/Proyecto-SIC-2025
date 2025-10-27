from django.db import models
from cuentas.models import Cuenta
# Create your models here
class Transaccion(models.Model):
    descripcion = models.CharField(max_length=150)
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.descripcion} - {self.fecha}"
    
    
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
    