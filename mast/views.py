from datetime import datetime
import operator

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Major, Course, Required_Classes_for_Track, Classes_Taken_by_Student, Grade, CourseStatus, \
    Comment, Student_Course_Schedule, Semester, Requirement_Semester, Season, Tracks_in_Major


def home(request):
    return render(request, 'mast/home.html', {})


def gpd_landing(request):
    return render(request, 'mast/gpd_landing.html', {})


def major_index(request):
    context = {'major_list': Major.objects.order_by('name')[1:],
               'course_list': Course.objects.all(),
               'track_list': Tracks_in_Major.objects.all()}
    return render(request, 'mast/major_index.html', context)


def add_student(request):
    context = {'major_list': Major.objects.order_by('name')[1:], 'semesters': Semester.objects.order_by('year'),
               'requirement_semesters': Requirement_Semester.objects.order_by('year')}
    return render(request, 'mast/new_student.html', context)


def commit_new_student(request):
    id_list = [i.sbu_id for i in Student.objects.all()]
    id_taken = False
    sbu_id = request.GET['sbu_id']
    first_name = request.GET['first_name']
    last_name = request.GET['last_name']
    email = request.GET['email']
    major = request.GET['major']
    entry_semester = request.GET['entry_semester']
    requirement_semester = request.GET['requirement_semester']
    try:
        if int(sbu_id) in id_list:
            id_taken = True
            raise Exception('non-unique id')
        student = Student(sbu_id=sbu_id,
                          first_name=first_name,
                          last_name=last_name,
                          email=email,
                          major=Major.objects.get(id=int(major)),
                          entry_semester=Semester.objects.get(id=int(entry_semester)),
                          requirement_semester=Requirement_Semester.objects.get(id=int(requirement_semester))
                          )
        student.save()
    except:
        if id_taken:
            return render(request, 'mast/new_student.html', {
                'major_list': Major.objects.order_by('name')[1:], 'semesters': Semester.objects.order_by('year'),
                'requirement_semesters': Requirement_Semester.objects.order_by('year'),
                'error_message': "ID taken."
            })
        else:
            return render(request, 'mast/new_student.html', {
                'major_list': Major.objects.order_by('name')[1:], 'semesters': Semester.objects.order_by('year'),
                'requirement_semesters': Requirement_Semester.objects.order_by('year'),
                'error_message': "Something went wrong."
            })
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


def detail(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    comment_list = Comment.objects.filter(student=sbu_id)
    semester_list = {i.course.semester: 1 for i in Student_Course_Schedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sorted(semester_list, key=operator.attrgetter('year'))
    return render(request, 'mast/detail.html', {'student': student,
                                                'major_list': Major.objects.order_by('name'),
                                                'classes_taken': Classes_Taken_by_Student.objects.all(),
                                                'comment_list': comment_list.order_by('post_date'),
                                                'semester_list': semester_list,
                                                'schedule': Student_Course_Schedule.objects.filter(student=sbu_id)
                                                })


def add_comment(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        new_comment = request.GET['new_comment']
        if new_comment == '':
            raise Exception
        c = Comment(student=student, text=str(new_comment), post_date=str(datetime.now()))
        c.save()
    except:
        return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))
