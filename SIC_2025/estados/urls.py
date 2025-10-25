from django.urls import path
from . import views

urlpatterns = [
    path('', views.estados_financieros, name='estados_financieros'),
]
