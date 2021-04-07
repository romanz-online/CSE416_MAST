from datetime import datetime
import operator

from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from django.shortcuts import get_object_or_404, render
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.urls import reverse
from .datatables import StudentDatatable
from .models import Student, Major, Season, CoursesTakenByStudent, Comment, StudentCourseSchedule, Semester, Track, \
    TrackCourseSet, CourseInTrackSet, CourseToCourseRelation, Department


def home(request):
    return render(request, 'mast/home.html', {})


def major_index(request):
    context = {'major_list': Major.objects.order_by('name')[1:],
               'track_list': Track.objects.all(),
               'track_course_sets': TrackCourseSet.objects.all(),
               'courses_in_sets': CourseInTrackSet.objects.all(),
               'course_relations': CourseToCourseRelation.objects.all()}
    return render(request, 'mast/major_index.html', context)


def commit_new_student(request):
    id_list = [i.sbu_id for i in Student.objects.all()]
    id_taken = False
    sbu_id = request.GET['sbu_id']
    first_name = request.GET['first_name']
    last_name = request.GET['last_name']
    email = request.GET['email']
    track = request.GET['major_track']
    track = Track.objects.get(id=track)
    major = track.major
    entry_semester = request.GET['entry_semester']
    entry_semester = Semester.objects.get(id=int(entry_semester))
    requirement_semester = request.GET['requirement_semester']
    requirement_semester = Semester.objects.get(id=int(requirement_semester))
    semesters_enrolled = 1

    if Semester.objects.filter(is_current_semester=True):
        current_semester = Semester.objects.filter(is_current_semester=True)[0]
        if entry_semester.year < current_semester.year:
            i = entry_semester.year
            count = 0
            while i < current_semester.year:
                if Semester.objects.filter(year=i):
                    count += Semester.objects.filter(year=i).count()
                i += 1
            count += 1
            if current_semester.season == Season.FALL:
                count += 1
            semesters_enrolled = count

    try:
        if int(sbu_id) in id_list:
            id_taken = True
            raise Exception('non-unique id')
        student = Student(sbu_id=sbu_id,
                          first_name=first_name,
                          last_name=last_name,
                          email=email,
                          major=major,
                          track=track,
                          unsatisfied_courses=track.total_requirements,
                          entry_semester=entry_semester,
                          requirement_semester=requirement_semester,
                          semesters_enrolled=semesters_enrolled
                          )
        student.save()
    except:
        if id_taken:
            return render(request, 'mast/student_index.html', {
                'major_list': Major.objects.order_by('name'),
                'semesters': Semester.objects.order_by('year'),
                'requirement_semesters': Semester.objects.order_by('year'),
                'student_list': Student.objects.order_by('sbu_id'),
                'error_message': "ID taken."
            })
        else:
            return render(request, 'mast/student_index.html', {
                'major_list': Major.objects.order_by('name'),
                'semesters': Semester.objects.order_by('year'),
                'requirement_semesters': Semester.objects.order_by('year'),
                'error_message': "Invalid or missing value.",
                'student_list': Student.objects.order_by('sbu_id')
            })
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


def detail(request, sbu_id):
    create_none_major()
    student = get_object_or_404(Student, pk=sbu_id)
    comment_list = Comment.objects.filter(student=sbu_id)
    semester_list = {i.course.semester: 1 for i in StudentCourseSchedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sorted(semester_list, key=operator.attrgetter('year'))
    return render(request, 'mast/detail.html', {'student': student,
                                                'major_list': Major.objects.order_by('name'),
                                                'classes_taken': CoursesTakenByStudent.objects.all(),
                                                'comment_list': comment_list.order_by('post_date'),
                                                'semester_list': semester_list,
                                                'schedule': StudentCourseSchedule.objects.filter(student=sbu_id)
                                                })


def add_comment(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        new_comment = request.GET['new_comment']
        if new_comment == '':
            raise Exception
        email_message = 'A Graduate Program Director has left a comment on your profile:\n"' + new_comment + '"'
        email = EmailMessage('New Comment from MAST', email_message, to=[str(student.email)])
        email.send()
        c = Comment(student=student, text=str(new_comment), post_date=str(datetime.now()))
        c.save()
        print(student.email)
    except:
        return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


<<<<<<< Updated upstream
def create_none_major():
    if not Major.objects.filter(department=Department.NONE):
        semester = Semester.objects.all()[0]
        none_major = Major(department=Department.NONE,
                           name='(None)',
                           requirement_semester=semester)
        none_major.save()
=======
def student_datatable(request):
    student = StudentDatatable()
    return render(request, 'mast/student_index.html', {'student': student})
>>>>>>> Stashed changes
