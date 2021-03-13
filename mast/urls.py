from django.urls import path

from . import views

app_name = 'mast'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:sbu_id>/', views.detail, name='detail'),
    path('search/', views.search, name='search'),
    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
]