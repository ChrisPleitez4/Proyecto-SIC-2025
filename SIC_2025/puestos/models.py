from django.db import models

class Puesto(models.Model):
    idPuesto = models.AutoField(primary_key=True)
    nombrePuesto = models.CharField(max_length=100)
    salarioHoraPuesto = models.FloatField()
    salarioDiarioPuesto = models.FloatField()
    salarioMesPuesto = models.FloatField()

    def __str__(self):
        return self.nombrePuesto

