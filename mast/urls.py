from django.urls import path

from . import views

app_name = 'mast'
urlpatterns = [
    path('', views.home, name='home'),
    path('gpd_landing', views.gpd_landing, name='gpd_landing'),
    path('student_index/', views.student_index, name='student_index'),
    path('new_student/', views.add_student, name='add_student'),
    path('commit_new_student/', views.commit_new_student, name='commit_new_student'),
    path('majors/', views.major_index, name='major_index'),
    path('<int:sbu_id>/', views.detail, name='detail'),
    path('edit/<int:sbu_id>/', views.edit, name='edit'),
    path('edit/<int:sbu_id>/commit_edit', views.commit_edit, name='commit_edit'),
    path('edit/<int:sbu_id>/add_taken_course', views.add_taken_course, name='add_taken_course'),
    path('student_index/search/', views.search, name='search'),
]