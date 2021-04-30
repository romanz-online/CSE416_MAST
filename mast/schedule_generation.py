from django.shortcuts import get_object_or_404, render

from .models import Student, CourseInstance


def schedule_generation(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    course_list = {i for i in CourseInstance.objects.all() if i.section != 999}
    context = {
        'student': student,
        'course_list': course_list
    }
    return render(request, 'mast/schedule_generation.html', context)
