from django.urls import path
from . import views, modifying_schedule, searching, editing_student, importing, schedule_generation, enrollment_trends, \
    rollover_semester, major_index, student_detail

app_name = 'mast'
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),

    path('edit/<int:sbu_id>/', editing_student.student_edit, name='student_edit'),
    path('edit/<int:sbu_id>/commit_edit', editing_student.student_commit_edit, name='student_commit_edit'),

    path('commit_new_student/', views.commit_new_student, name='commit_new_student'),

    path('majors/', major_index.major_index, name='major_index'),
    path('courses/', views.course_index, name='course_index'),

    path('<int:sbu_id>/', student_detail.detail, name='detail'),
    path('<int:sbu_id>/add_comment', student_detail.add_comment, name='add_comment'),

    path('student_index/import_student/', importing.import_student, name='import_student'),
    path('student_index/import_grades/', importing.import_grades, name='import_grades'),
    path('student_index/import_grades_stub/', importing.import_grades_stub, name='import_grades_stub'),
    path('import_courses/', importing.import_courses, name="import_courses"),
    path('import_degree_requirements/', importing.import_degree_requirements, name="import_degree_requirements"),
    path('scrape_courses/', importing.scrape_courses, name="scrape_courses"),

    path('edit_schedule/<int:sbu_id>/', modifying_schedule.edit_schedule, name='edit_schedule'),
    path('edit_schedule/<int:sbu_id>/add_scheduled_course/', modifying_schedule.add_scheduled_course,
         name='add_scheduled_course'),
    path('edit_schedule/<int:sbu_id>/modify_scheduled_course/<int:course>', modifying_schedule.modify_scheduled_course,
         name='modify_scheduled_course'),
    path('edit_schedule/<int:sbu_id>/add_scheduled_semester/', modifying_schedule.add_scheduled_semester,
         name='add_scheduled_semester'),

    path('schedule_gen/<int:sbu_id>/', schedule_generation.schedule_generation, name='schedule_gen'),
    path('schedule_gen/<int:sbu_id>/generate', schedule_generation.generate_schedule, name='generate'),
    path('schedule_gen/<int:sbu_id>/smart_suggest', schedule_generation.smart_suggest, name='smart_suggest'),
    path('offered_schedules/<int:sbu_id>/', schedule_generation.offered_schedules, name='offered_schedules'),
    path('offered_schedules/<int:sbu_id>/<int:schedule_id>', schedule_generation.schedule_display,
         name='display_schedule'),
    path('offered_schedules/<int:sbu_id>/<int:schedule_id>/<int:course_id>',
         schedule_generation.approve_scheduled_course, name='approve_scheduled_course'),
    path('offered_schedules/<int:sbu_id>/<int:schedule_id>/approve_all', schedule_generation.approve_all,
         name='approve_all'),

    path('edit/<int:sbu_id>/', editing_student.edit, name='edit'),
    path('edit/<int:sbu_id>/delete_record', editing_student.delete_record, name='delete_record'),
    path('edit/<int:sbu_id>/commit_edit', editing_student.commit_edit, name='commit_edit'),
    path('edit/<int:sbu_id>/add_taken_course', editing_student.add_taken_course, name='add_taken_course'),
    path('edit/<int:sbu_id>/add_transfer_course', editing_student.add_transfer_course, name='add_transfer_course'),
    path('edit/<int:sbu_id>/modify_course_in_progress/<int:record>', editing_student.modify_course_in_progress,
         name='modify_course_in_progress'),

    path('student_index/', searching.student_index, name='student_index'),
    path('student_index/search/', searching.search, name='search'),
    path('student_index/#', searching.delete_all_students, name='delete_all_students'),

    path('<str:course_department>/<int:course_number>/<int:section>', views.course_detail, name='course_detail'),

    path('enrollment_trends', enrollment_trends.enrollment_trends, name='enrollment_trends'),
    path('enrollment_trends/specify', enrollment_trends.enrollment_trends_specify, name='specify'),

    path('rollover_semester', rollover_semester.rollover_semester_page, name='rollover_semester_page'),
    path('rollover_semester/#', rollover_semester.rollover_semester, name='rollover_semester'),
]
