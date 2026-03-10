from django.urls import path
from . import views

app_name = "navis"

urlpatterns = [
    path("", views.index, name="index"),
]
