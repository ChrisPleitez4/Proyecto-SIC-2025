from django.db import models
from decimal import Decimal

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
    saldo_final = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.codCuenta} - {self.nombreCuenta}"

    # ---------------------------------------
    # 🔹 Saldo de la cuenta según naturaleza
    # ---------------------------------------
    def saldo_cuenta(self):
        """Devuelve el saldo actual de la cuenta según su naturaleza contable."""
        tipo = self.subTipoCuenta.tipoCuenta.codTipoCuenta[0]  # 1, 2, 3, 4 o 5

        if tipo == '1':  # Activo
            return self.debe - self.haber
        elif tipo in ['2', '3']:  # Pasivo o Capital
            return self.haber - self.debe
        elif tipo == '4':  # Gastos
            return self.debe - self.haber
        elif tipo == '5':  # Ingresos
            return self.haber - self.debe
        else:
            return "Saldo Cero"

    # ---------------------------------------
    # 🔹 Tipo de saldo (deudor / acreedor)
    # ---------------------------------------
    def tipo_saldo(self):
        saldo = self.saldo_cuenta()
        if saldo > 0:
            return "Deudor" if self.subTipoCuenta.tipoCuenta.codTipoCuenta[0] in ['1', '4'] else "Acreedor"
        elif saldo < 0:
            return "Acreedor" if self.subTipoCuenta.tipoCuenta.codTipoCuenta[0] in ['1', '4'] else "Deudor"
        return "Saldo Cero"

    def es_ingreso(self):
        return self.codCuenta.startswith('51')