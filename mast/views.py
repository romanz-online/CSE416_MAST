from datetime import datetime

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .datatables import StudentDatatable
from .models import Student, Major, Season, Semester, Track, Course, CoursePrerequisiteSet, Prerequisite, \
    CourseInstance

from . import searching, student_detail, editing_student


def setup():
    if not Group.objects.filter(name='Director'):
        director_group = Group(name='Director')
        director_group.save()

        AMS_director = User.objects.create_user('AMSDirector', 'mast.stonybrook@gmail.com', 'amspassword')
        AMS_director.save()
        AMS_director.groups.add(director_group)
        CSE_director = User.objects.create_user('CSEDirector', 'mast.stonybrook@gmail.com', 'csepassword')
        CSE_director.save()
        CSE_director.groups.add(director_group)
        BMI_director = User.objects.create_user('BMIDirector', 'mast.stonybrook@gmail.com', 'bmipassword')
        BMI_director.save()
        BMI_director.groups.add(director_group)
        ESE_director = User.objects.create_user('ESEDirector', 'mast.stonybrook@gmail.com', 'esepassword')
        ESE_director.save()
        ESE_director.groups.add(director_group)

    if not Group.objects.filter(name='Student'):
        student_group = Group(name='Student')
        student_group.save()

    spring = range(80, 172)
    summer = range(172, 264)
    fall = range(264, 355)
    doy = datetime.today().timetuple().tm_yday
    if not len(Semester.objects.all()):
        current_year = int(datetime.today().year)
        for year in range(current_year - 5, current_year + 20):
            for season in Season.choices:
                if not season[0] == Season.NOT_APPLICABLE:
                    new_semester = Semester(season=season[0], year=year)
                    if year == current_year:
                        if doy in spring and season[0] == Season.SPRING:
                            new_semester.is_current_semester = True
                        elif doy in summer and season[0] == Season.SUMMER:
                            new_semester.is_current_semester = True
                        elif doy in fall and season[0] == Season.FALL:
                            new_semester.is_current_semester = True
                        elif doy not in spring and doy not in summer and doy not in fall and season[0] == Season.WINTER:
                            new_semester.is_current_semester = True
                        else:
                            new_semester.is_current_semester = False

                    if new_semester not in Semester.objects.all():
                        new_semester.save()
    if not Major.objects.filter(department='N/A'):
        semester = Semester.objects.all()[0]
        none_major = Major(department='N/A',
                           name='(None)',
                           requirement_semester=semester)
        none_major.save()


def home(request):
    setup()
    return render(request, 'mast/home.html', {})


@login_required
def login(request):
    if request.user.groups.filter(name='Student'):
        return student_detail.detail(request, request.user.username)
    else:
        return searching.student_index(request)


@login_required
def course_index(request):
    is_student = False
    student = None
    if request.user.groups.filter(name='Student'):
        is_student = True
        sbu_id = request.user.username
        student = get_object_or_404(Student, pk=sbu_id)

    course_list = {i for i in CourseInstance.objects.all() if i.section != 999}
    context = {
        'course_list': course_list,
        'is_student': is_student,
        'student': student,
    }
    return render(request, 'mast/course_index.html', context)


@login_required
def commit_new_student(request):
    if request.user.groups.filter(name='Student'):
        return render(request, 'mast/home.html', {None: None})

    id_list = [i.sbu_id for i in Student.objects.all()]
    id_taken = False
    sbu_id = request.GET['sbu_id']
    first_name = request.GET['first_name']
    last_name = request.GET['last_name']
    password = request.GET['password']
    password.replace('\r', '')
    email = request.GET['email']
    entry_semester = request.GET['entry_semester']
    entry_semester = Semester.objects.get(id=int(entry_semester))

    dummy_track = request.GET['major_track']
    dummy_track = Track.objects.get(id=dummy_track)
    latest_track = Track.objects.filter(name=dummy_track.name)[0]
    for i in Track.objects.filter(name=dummy_track.name):
        if i.major.requirement_semester.year > latest_track.major.requirement_semester.year:
            latest_track = i
        if i.major.requirement_semester.season == Season.WINTER:
            latest_track = i
        elif i.major.requirement_semester.season == Season.FALL and (
                latest_track.major.requirement_semester.season == Season.SPRING or
                latest_track.major.requirement_semester.season == Season.SUMMER):
            latest_track = i
        elif i.major.requirement_semester.season == Season.SUMMER and \
                latest_track.major.requirement_semester.season == Season.SPRING:
            latest_track = i

    track = latest_track
    major = track.major
    requirement_semester = major.requirement_semester

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
                          password=password,
                          major=major,
                          track=track,
                          unsatisfied_courses=track.total_requirements,
                          entry_semester=entry_semester,
                          requirement_semester=requirement_semester,
                          semesters_enrolled=semesters_enrolled,
                          )
        student.save()

        editing_student.sync_course_data(student)

        student_user = User.objects.create_user(student.sbu_id, student.email, student.password)
        student_user.save()
        student_user.groups.add(Group.objects.filter(name='Student')[0])
    except:
        current_user = request.user.username
        if current_user != "admin": 
            current_user = current_user[0:3]
        track_list = []
        found = False
        for i in Track.objects.all():
            for j in track_list:
                if i.name == j.name and i.major.name == j.major.name:
                    found = True
            if not found:
                track_list.append(i)
        if id_taken:
            return render(request, 'mast/student_index.html', {
                'major_list': Major.objects.order_by('name'),
                'semesters': Semester.objects.order_by('year'),
                'requirement_semesters': Semester.objects.order_by('year'),
                'student_list': Student.objects.order_by('sbu_id'),
                'error_message': "ID taken.",
                'current_user': current_user,
                'track_list': track_list 
            })
        else:
            return render(request, 'mast/student_index.html', {
                'major_list': Major.objects.order_by('name'),
                'semesters': Semester.objects.order_by('year'),
                'requirement_semesters': Semester.objects.order_by('year'),
                'error_message': "Invalid or missing value.",
                'student_list': Student.objects.order_by('sbu_id'),
                'current_user': current_user,
                'track_list': track_list 
            })
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


@login_required
def course_detail(request, course_department, course_number, section):
    course = Course.objects.get(department=course_department, number=course_number)
    course_instance = CourseInstance.objects.get(course=course, section=section)
    prerequisite_string = 'None.'
    if CoursePrerequisiteSet.objects.filter(parent_course=course_instance):
        prerequisite_set = CoursePrerequisiteSet.objects.filter(parent_course=course_instance)[0]
        prerequisite_string = ''
        course_start = True
        set_start = True
        for prerequisite in Prerequisite.objects.filter(course_set=prerequisite_set):
            if not course_start:
                prerequisite_string += ','
            prerequisite_string += str(prerequisite.course.course)
            course_start = False
        if not course_start:
            if prerequisite_string[len(prerequisite_string) - 1] == ',':
                prerequisite_string = prerequisite_string[:-1]
            prerequisite_string += '\n'
        for nested_set in CoursePrerequisiteSet.objects.filter(parent_set=prerequisite_set):
            for prerequisite in Prerequisite.objects.filter(course_set=nested_set):
                if not set_start:
                    prerequisite_string += ' or '
                prerequisite_string += str(prerequisite.course.course)
                set_start = False
            if not set_start:
                prerequisite_string += '\n'
            set_start = True

    return render(request, 'mast/course_detail.html', {'course': course_instance,
                                                       'prerequisites': prerequisite_string
                                                       })


@login_required
def student_datatable(request):
    if request.user.groups.filter(name='Student'):
        return render(request, 'mast/home.html', {None: None})

    student = StudentDatatable()
    return render(request, 'mast/student_index.html', {'student': student})
