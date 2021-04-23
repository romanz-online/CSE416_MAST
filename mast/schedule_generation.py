from django.shortcuts import get_object_or_404, render

from .models import Student


def schedule_generation(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    context = {
        'student': student,
    }
    return render(request, 'mast/schedule_generation.html', context)
