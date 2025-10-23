from django.urls import path
from . import views

urlpatterns = [
    path("registrar/", views.registrar_puesto, name="registrar_puesto"),
]