from django.urls import path, include
from . import views

app_name = 'dns_records'
urlpatterns = [
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('dump', views.dump, name='dump-system'),
    path('main', views.main, name='main'),
    path('rebuild', views.rebuild_db, name='rebuild'),
    path('schedule/rebuild', views.cache_setup, name='automate-rebuild'),
] 
