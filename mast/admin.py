from django.contrib import admin
from .models import Student, Major, Course, CoursesTakenByStudent, StudentCourseSchedule, Comment, Track, Semester, \
    CourseInstance, Prerequisite, CoursePrerequisiteSet, TrackCourseSet, CourseInTrackSet

admin.site.register(Student)
admin.site.register(Semester)
admin.site.register(Major)
admin.site.register(Course)
admin.site.register(CourseInstance)
admin.site.register(CoursesTakenByStudent)
admin.site.register(Comment)
admin.site.register(StudentCourseSchedule)
admin.site.register(Track)
admin.site.register(Prerequisite)
admin.site.register(CoursePrerequisiteSet)
admin.site.register(TrackCourseSet)
admin.site.register(CourseInTrackSet)
