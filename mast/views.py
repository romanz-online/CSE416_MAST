from datetime import datetime
import operator

from django.shortcuts import get_object_or_404, render
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.urls import reverse
from .datatables import StudentDatatable
from .models import Student, Major, Season, CoursesTakenByStudent, Comment, StudentCourseSchedule, Semester, Track, \
    TrackCourseSet, CourseInTrackSet, CourseToCourseRelation, Course, CoursePrerequisiteSet, Prerequisite


def setup():
    if not Major.objects.filter(department='N/A'):
        semester = Semester.objects.all()[0]
        none_major = Major(department='N/A',
                           name='(None)',
                           requirement_semester=semester)
        none_major.save()
    spring = range(80, 172)
    summer = range(172, 264)
    fall = range(264, 355)
    doy = datetime.today().timetuple().tm_yday
    if not len(Semester.objects.all()):
        current_year = int(datetime.today().year)
        for year in range(current_year-5, current_year+5):
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
                        else:
                            new_semester.is_current_semester = True
                    new_semester.save()


def home(request):
    setup()
    return render(request, 'mast/home.html', {})


def display_set_info(course_set, layer):
    if course_set.parent_course_set:
        if course_set.parent_course_set.size and not course_set.size:
            for i in range(layer):
                print('-', end='')
            print('The following courses will not satisfy the requirement:')
    elif not course_set.parent_course_set and not course_set.size:
        for i in range(layer):
            print('-', end='')
        print('The following courses will not satisfy the requirement:')

    for course in CourseInTrackSet.objects.filter(course_set=course_set):
        for i in range(layer):
            print('-', end='')
        if course.how_many_semesters > 1:
            print(str(course) + ', taken at least ' + str(course.how_many_semesters) + ' times.')
        else:
            print(str(course))

    if not course_set.size and course_set.lower_limit != 100 and course_set.upper_limit != 999 and course_set.department_limit != 'N/A':
        for i in range(layer-1):
            print('-', end='')
        print(course_set.department_limit + str(course_set.lower_limit) + '-' + course_set.department_limit + str(course_set.upper_limit))

    for nested_set in TrackCourseSet.objects.filter(parent_course_set=course_set):
        display_set_info(nested_set, layer+1)


def display_track_info(track):
    print(str(track.number_of_areas) + ' areas must be completed from the following:')
    for course_set in TrackCourseSet.objects.filter(track=track, parent_course_set=None):
        if course_set.size:
            if course_set.limiter:
                print('At most ' + str(course_set.size) + ' course(s) from ' + course_set.name + ':')
            else:
                print(str(course_set.size) + ' course(s) from ' + course_set.name + ':')
        display_set_info(course_set, 0)



def major_index(request):
    # for track in Track.objects.all():
    #     display_track_info(track)
    display_track_info(Track.objects.filter(name='Advanced Project')[0])
    context = {'major_list': Major.objects.order_by('name')[1:],
               'track_list': Track.objects.all(),
               'track_course_sets': TrackCourseSet.objects.all(),
               'courses_in_sets': CourseInTrackSet.objects.all(),
               'course_relations': CourseToCourseRelation.objects.all(),
               'course_list': Course.objects.all()}
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


def course_detail(request, course_department, course_number):
    course = get_object_or_404(Course, department=course_department, number=course_number)
    return render(request, 'mast/course_detail.html', {'course': course,
                                                       'prerequisite_set_list': CoursePrerequisiteSet.objects.all(),
                                                       'prerequisite_list': Prerequisite.objects.all()
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


def student_datatable(request):
    student = StudentDatatable()
    return render(request, 'mast/student_index.html', {'student': student})
