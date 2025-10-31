from django.urls import path
from . import views

urlpatterns = [
    path("", views.libro_mayor, name="libro_mayor"),
    path('detalle/<int:transaccion_id>/', views.detalle_transaccion_libromayor, name='detalle_transaccion_libromayor'),
]