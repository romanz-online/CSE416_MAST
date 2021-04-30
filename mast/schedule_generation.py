from django.shortcuts import get_object_or_404, render

from .models import Student, CourseInstance, CoursePrerequisiteSet, Prerequisite


def schedule_generation(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    course_list = {i for i in CourseInstance.objects.all() if i.section != 999}
    context = {
        'student': student,
        'course_list': course_list
    }
    return render(request, 'mast/schedule_generation.html', context)


#returns boolean indicating if all class prereqs have been met in a given schedule or not
def prereqs_met(student, course, schedule_id):
    student_courses = StudentCourseSchedule.objects.filter(student=student, schedule_id=schedule_id) | StudentCourseSchedule.objects.filter(student=student, schedule_id=0)
    prereq_set = CoursePrerequisiteSet.objects.filter(parent_course=course)
    for prereq in Prerequisite.objects.filter(course_set=prereq_set):
        if prereq not in student_courses:
            return False

    for nested_set in CoursePrerequisiteSet.objects.filter(parent_set=prereq_set):
        met = False
        for prereq in Prerequisite.objects.filter(course_set=nested_set):
            if prereq in student_courses:
                met = True
        if not met:
            return False

    return True 