from django.urls import path
from . import views

urlpatterns = [
    path("registrar/", views.Registrar_proyecto, name="Registrar_proyecto"),
]