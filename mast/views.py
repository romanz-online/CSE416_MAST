from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Major, Required_Classes_for_Major, Classes_Taken_by_Student


def home(request):
    return render(request, 'mast/home.html', {})


def gpd_landing(request):
    return render(request, 'mast/gpd_landing.html', {})


def major_index(request):
    context = {'major_list': Major.objects.order_by('name'), 'required_classes_for_major_list': Required_Classes_for_Major.objects.order_by('major')}
    return render(request, 'mast/major_index.html', context)


def student_index(request):
    context = {'student_list': Student.objects.order_by('sbu_id'), 'major_list': Major.objects.order_by('name')}
    return render(request, 'mast/student_index.html', context)


def search(request):
    name_search = request.GET['name']
    sbu_id_search = request.GET['sbu_id']
    major_search = request.GET['major']
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

    m = Major.objects.get(id=int(major_search))
    if m.name != '(None)':
        name_list = name_list.filter(major=m)
        sbu_id_list = sbu_id_list.filter(major=m)

    student_list = list(set(name_list) & set(sbu_id_list))
    context = {'student_list': student_list,
               'major_list': Major.objects.order_by('name'),
               'name_search': name_search,
               'sbu_id_search': sbu_id_search,
               'graduated_search': graduated_search,
               'withdrew_search': withdrew_search,
               'major_search': int(major_search)}
    return render(request, 'mast/student_index.html', context)


def detail(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    return render(request, 'mast/detail.html', {'student': student,
                                                'major_list': Major.objects.order_by('name'),
                                                'classes_taken': Classes_Taken_by_Student.objects.all()})


def edit(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    return render(request, 'mast/edit.html', {'student': student, 'major_list': Major.objects.order_by('name')})


def commit_edit(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        name = request.GET['name']
        email = request.GET['email']
        major = request.GET['major']
        graduated = True if request.GET['graduated'] == 'yes' else False
        withdrew = True if request.GET['withdrew'] == 'yes' else False
        entry_season = request.GET['entry_season']
        graduation_season = request.GET['graduation_season']
        requirement_season = request.GET['requirement_season']
        entry_year = request.GET['entry_year']
        graduation_year = request.GET['graduation_year']
        requirement_year = request.GET['requirement_year']
        student.name = name
        student.email = email
        student.major = Major.objects.get(id=int(major))
        student.graduated = graduated
        student.withdrew = withdrew
        student.entry_semester_season = entry_season
        student.entry_semester_year = entry_year
        student.graduation_semester_season = graduation_season
        student.graduation_semester_year = graduation_year
        student.requirement_semester_season = requirement_season
        student.requirement_semester_year = requirement_year
        student.save()
    except:
        student = get_object_or_404(Student, pk=sbu_id)
        return render(request, 'mast/edit.html', {
            'student': student,
            'major_list': Major.objects.order_by('name'),
            'error_message': "Something went wrong.",
        })
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))
