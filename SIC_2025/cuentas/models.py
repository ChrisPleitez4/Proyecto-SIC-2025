from django.db import models

# Create your models here.
# MODELO PARA TIPOCUENTA

class TipoCuenta(models.Model):
    codTipoCuenta = models.CharField(max_length=10, unique=True)
    nombreRubro = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.codTipoCuenta}- {self.nombreRubro}"
    

#MODELO PARA EL SUBTIPO DE CUENTA 
class SubTipoCuenta(models.Model):
    codSubTipoCuenta = models.CharField(max_length=10, unique=True)
    nombreSubCuenta = models.CharField(max_length=100)
    tipoCuenta = models.ForeignKey(TipoCuenta, on_delete=models.CASCADE,related_name='subtipos')
    
    def __str__(self):
        return f"{self.codSubTipoCuenta}- {self.nombreSubCuenta}"

#MDOELO PARA LA CUENTA 
class Cuenta(models.Model):
    codCuenta = models.CharField(max_length=10, unique=True)
    nombreCuenta = models.CharField(max_length=100)
    subTipoCuenta = models.ForeignKey(SubTipoCuenta, on_delete=models.CASCADE,related_name='cuentas')
    debe = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    haber = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    def __str__(self):
        return f"{self.codCuenta} - {self.nombreCuenta}"


    def saldo_cuenta(self):
        saldo =self.debe - self.haber
        return saldo

    def tipo_saldo(self):
        saldo =self.debe - self.haber
        if saldo > 0:
            return "Deudor"
        elif saldo < 0:
            return "Acreedor"
        else:
            return "Saldo Cero"