from django.shortcuts import get_object_or_404, render
from .models import Student


def index(request):
    context = {'student_list': Student.objects.order_by('sbu_id')}
    return render(request, 'mast/index.html', context)


def search(request):
    name_search = request.GET['name']
    sbu_id_search = request.GET['sbu_id']
    name_list = Student.objects.filter(name__icontains=name_search)
    sbu_id_list = Student.objects.filter(sbu_id__icontains=sbu_id_search)
    student_list = list(set(name_list) & set(sbu_id_list))
    context = {'student_list': student_list, 'name_search': name_search, 'sbu_id_search': sbu_id_search}
    return render(request, 'mast/index.html', context)


def detail(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    return render(request, 'mast/detail.html', {'student': student})