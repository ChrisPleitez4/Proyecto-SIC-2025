from django.db import models

class Puesto(models.Model):
    idPuesto = models.AutoField(primary_key=True)
    nombrePuesto = models.CharField(max_length=100, unique=True)
    salarioHoraPuesto = models.DecimalField(max_digits=12, decimal_places=2)
    salarioDiarioPuesto = models.DecimalField(max_digits=12, decimal_places=2)
    salarioMesPuesto = models.DecimalField(max_digits=12, decimal_places=2)
    administrativo=models.BooleanField(default=False)

    def __str__(self):
        return self.nombrePuesto

