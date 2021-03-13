from django.shortcuts import get_object_or_404, render
from .models import Student


def index(request):
    context = {'student_list': Student.objects.order_by('sbu_id')}
    return render(request, 'mast/index.html', context)


def search(request):
    search = request.GET['query']
    student_list = Student.objects.filter(sbu_id__icontains=search)
    context = {'student_list': student_list, 'search': search}
    return render(request, 'mast/search.html', context)


def detail(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    return render(request, 'mast/detail.html', {'student': student})