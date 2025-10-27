from django.urls import path
from . import views

urlpatterns = [
    path('', views.transacciones_vista, name='transacciones'),
]
