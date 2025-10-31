from django.urls import path
from costosventa.views import calcular_costo, guardar_anticipo

urlpatterns = [
    path('', calcular_costo, name='calcular_costo'),
    path('guardar_anticipo/', guardar_anticipo, name='guardar_anticipo'),
]