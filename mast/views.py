from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Major, Course, Required_Classes_for_Major, Classes_Taken_by_Student, Grade


def home(request):
    return render(request, 'mast/home.html', {})


def gpd_landing(request):
    return render(request, 'mast/gpd_landing.html', {})


def major_index(request):
    context = {'major_list': Major.objects.order_by('name')[1:],
               'required_classes_for_major_list': Required_Classes_for_Major.objects.order_by('major')}
    return render(request, 'mast/major_index.html', context)


def add_student(request):
    context = {'major_list': Major.objects.order_by('name')}
    return render(request, 'mast/new_student.html', context)


def commit_new_student(request):
    try:
        id_list = [i.sbu_id for i in Student.objects.all()]
        sbu_id = min(id_list)
        while sbu_id in id_list:
            sbu_id += 1
        if sbu_id > 999999999:
            raise Exception('No IDs available in the current range.')
        name = request.GET['name']
        email = request.GET['email']
        major = request.GET['major']
        entry_season = request.GET['entry_season']
        graduation_season = request.GET['graduation_season']
        requirement_season = request.GET['requirement_season']
        entry_year = int(request.GET['entry_year'])
        graduation_year = int(request.GET['graduation_year'])
        requirement_year = int(request.GET['requirement_year'])
        student = Student(sbu_id=sbu_id,
                          name=name,
                          email=email,
                          major=Major.objects.get(id=int(major)),
                          entry_semester_season=entry_season,
                          entry_semester_year=entry_year,
                          graduation_semester_season=graduation_season,
                          graduation_semester_year=graduation_year,
                          requirement_semester_season=requirement_season,
                          requirement_semester_year=requirement_year)
        student.save()
    except:
        return render(request, 'mast/new_student.html', {
            'major_list': Major.objects.order_by('name'),
            'error_message': "Something went wrong."
        })
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


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
    grade_list = [i[0] for i in Grade.choices]
    return render(request, 'mast/edit.html', {'student': student,
                                              'major_list': Major.objects.order_by('name'),
                                              'course_list': Course.objects.order_by('name'),
                                              'classes_taken': Classes_Taken_by_Student.objects.all(),
                                              'grade_list': grade_list})


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
        for course in Classes_Taken_by_Student.objects.all():
            if course.student == student:
                new_grade = request.GET[str(course.id)]
                if course.grade != new_grade:
                    course.grade = new_grade
                    course.save()
        student.save()
    except:
        student = get_object_or_404(Student, pk=sbu_id)
        grade_list = [i[0] for i in Grade.choices]
        return render(request, 'mast/edit.html', {'student': student,
                                                  'major_list': Major.objects.order_by('name'),
                                                  'course_list': Course.objects.order_by('name'),
                                                  'classes_taken': Classes_Taken_by_Student.objects.all(),
                                                  'grade_list': grade_list,
                                                  'error_message': "Something went wrong."
                                                  })
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


def add_taken_course(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    grade_list = [i[0] for i in Grade.choices]
    try:
        new_course = request.GET['course']
        print('NEW COURSE:', new_course)
        new_course = Course.objects.get(id=new_course)
        new_grade = request.GET['grade']
        c = Classes_Taken_by_Student(student=student, course=new_course, grade=new_grade)
        c.save()
    except:
        return render(request, 'mast/edit.html', {'student': student,
                                                  'major_list': Major.objects.order_by('name'),
                                                  'course_list': Course.objects.order_by('name'),
                                                  'classes_taken': Classes_Taken_by_Student.objects.all(),
                                                  'grade_list': grade_list,
                                                  'error_message': "Something went wrong."
                                                  })
    return render(request, 'mast/edit.html', {'student': student,
                                              'major_list': Major.objects.order_by('name'),
                                              'course_list': Course.objects.order_by('name'),
                                              'classes_taken': Classes_Taken_by_Student.objects.all(),
                                              'grade_list': grade_list
                                              })
