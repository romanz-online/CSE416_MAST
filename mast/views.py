from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student


def index(request):
    context = {'student_list': Student.objects.order_by('sbu_id')}
    return render(request, 'mast/index.html', context)


def search(request):
    name_search = request.GET['name']
    sbu_id_search = request.GET['sbu_id']
    graduated_search = True if request.GET['graduated'] == 'yes' else False
    withdrew_search = True if request.GET['withdrew'] == 'yes' else False
    name_list = Student.objects.filter(name__icontains=name_search)
    sbu_id_list = Student.objects.filter(sbu_id__icontains=sbu_id_search)

    if not graduated_search:
        name_list = name_list.filter(graduated=False)
        sbu_id_list = sbu_id_list.filter(graduated=False)
    if not withdrew_search:
        name_list = name_list.filter(withdrew=False)
        sbu_id_list = sbu_id_list.filter(withdrew=False)

    student_list = list(set(name_list) & set(sbu_id_list))
    context = {'student_list': student_list,
               'name_search': name_search,
               'sbu_id_search': sbu_id_search,
               'graduated_search': graduated_search,
               'withdrew_search': withdrew_search}
    return render(request, 'mast/index.html', context)


def detail(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    return render(request, 'mast/detail.html', {'student': student})


def edit(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    return render(request, 'mast/edit.html', {'student': student})


def commit_edit(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        name = request.GET['name']
        email = request.GET['email']
        graduated = True if request.GET['graduated'] == 'yes' else False
        withdrew = True if request.GET['withdrew'] == 'yes' else False
        student.name = name
        student.email = email
        student.graduated = graduated
        student.withdrew = withdrew
        student.save()
    except:
        student = get_object_or_404(Student, pk=sbu_id)
        return render(request, 'mast/edit.html', {
            'student': student,
            'error_message': "Something went wrong.",
        })
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))
