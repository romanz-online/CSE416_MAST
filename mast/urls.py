from django.urls import path

from . import views, modifying_schedule, searching, editing_student, importing

app_name = 'mast'
urlpatterns = [
    path('', views.home, name='home'),
    path('gpd_landing', views.gpd_landing, name='gpd_landing'),
    path('new_student/', views.add_student, name='add_student'),
    path('commit_new_student/', views.commit_new_student, name='commit_new_student'),
    path('majors/', views.major_index, name='major_index'),
    path('<int:sbu_id>/', views.detail, name='detail'),
    path('<int:sbu_id>/add_comment', views.add_comment, name='add_comment'),
    path('import_student', importing.import_student, name='import_student'),
    path('import_courses', importing.import_courses, name="import_courses"),

    path('edit_schedule/<int:sbu_id>/', modifying_schedule.edit_schedule, name='edit_schedule'),
    path('edit_schedule/<int:sbu_id>/add_scheduled_course/', modifying_schedule.add_scheduled_course, name='add_scheduled_course'),
    path('edit_schedule/<int:sbu_id>/remove_scheduled_course/<int:course>', modifying_schedule.remove_scheduled_course,
         name='remove_scheduled_course'),
    path('edit_schedule/<int:sbu_id>/add_scheduled_semester/', modifying_schedule.add_scheduled_semester,
         name='add_scheduled_semester'),

    path('edit/<int:sbu_id>/', editing_student.edit, name='edit'),
    path('edit/<int:sbu_id>/delete_record', editing_student.delete_record, name='delete_record'),
    path('edit/<int:sbu_id>/commit_edit', editing_student.commit_edit, name='commit_edit'),
    path('edit/<int:sbu_id>/add_taken_course', editing_student.add_taken_course, name='add_taken_course'),
    path('edit/<int:sbu_id>/modify_course_in_progress/<int:record>', editing_student.modify_course_in_progress,
         name='modify_course_in_progress'),

    path('student_index/', searching.student_index, name='student_index'),
    path('student_index/search/', searching.search, name='search'),
    path('student_index/search/sort_by_id', searching.sort_by_id, name='sort_by_id'),
    path('student_index/search/sort_by_name', searching.sort_by_name, name='sort_by_name'),
    path('student_index/search/sort_by_graduation', searching.sort_by_graduation, name='sort_by_graduation'),
    path('student_index/search/sort_by_attendance', searching.sort_by_attendance, name='sort_by_attendance'),
]
