from django.contrib import admin
from .models import Student, Major, Course, Required_Classes_for_Major

admin.site.register(Student)
admin.site.register(Major)
admin.site.register(Course)
admin.site.register(Required_Classes_for_Major)