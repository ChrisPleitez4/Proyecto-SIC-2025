from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_periodos, name='lista_periodos'),
    path("crear/", views.crear_periodo, name="crear_periodo"),
    path("cerrar/<int:pk>/", views.cerrar_periodo, name="cerrar_periodo"),
]
