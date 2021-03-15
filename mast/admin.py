from django.contrib import admin
from .models import Student, Major, Course, Required_Classes_for_Major, Classes_Taken_by_Student, Comment

admin.site.register(Student)
admin.site.register(Major)
admin.site.register(Course)
admin.site.register(Required_Classes_for_Major)
admin.site.register(Classes_Taken_by_Student)
admin.site.register(Comment)