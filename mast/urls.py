from django.urls import path, include

from . import views

app_name = 'mast'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:sbu_id>/', views.detail, name='detail'),
    path('edit/<int:sbu_id>/', views.edit, name='edit'),
    path('search/', views.search, name='search'),
]