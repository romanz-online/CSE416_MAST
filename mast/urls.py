from django.urls import path

from . import views

app_name = 'mast'
urlpatterns = [
    path('', views.home, name='home'),
    path('gpd_landing', views.gpd_landing, name='gpd_landing'),
    path('student_index/', views.student_index, name='student_index'),
    path('majors/', views.major_index, name='major_index'),
    path('<int:sbu_id>/', views.detail, name='detail'),
    path('edit/<int:sbu_id>/', views.edit, name='edit'),
    path('commit_edit/<int:sbu_id>/', views.commit_edit, name='commit_edit'),
    path('student_index/search/', views.search, name='search'),
]