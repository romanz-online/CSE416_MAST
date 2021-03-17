from django.contrib import admin
from .models import Student, Major, Course, Required_Classes_for_Track, Classes_Taken_by_Student, Student_Course_Schedule, Comment, Tracks_in_Major

admin.site.register(Student)
admin.site.register(Major)
admin.site.register(Course)
admin.site.register(Required_Classes_for_Track)
admin.site.register(Classes_Taken_by_Student)
admin.site.register(Comment)
admin.site.register(Student_Course_Schedule)
admin.site.register(Tracks_in_Major)