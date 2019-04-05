from django.urls import path, include
from . import views

app_name = 'dns_records'
urlpatterns = [
    path('add_domain', views.add_domain, name='add-domain'),
] 