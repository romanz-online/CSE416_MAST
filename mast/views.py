from datetime import datetime
import operator

from django.shortcuts import get_object_or_404, render
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.urls import reverse
from .datatables import StudentDatatable
from .models import Student, Major, Season, CoursesTakenByStudent, Comment, StudentCourseSchedule, Semester, Track, \
    TrackCourseSet, CourseInTrackSet, CourseToCourseRelation, Course, CoursePrerequisiteSet, Prerequisite, \
    CourseInstance


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
        for year in range(current_year - 5, current_year + 5):
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


def course_index(request):
    course_list = {i for i in CourseInstance.objects.all() if i.section != 999}
    return render(request, 'mast/course_index.html', {'course_list': course_list})


def display_set_info(course_set, layer, info):
    # all this section does is create the sentences before each set of courses
    if course_set.parent_course_set and course_set.parent_course_set.size and not course_set.size:
        for i in range(layer - 1):
            info += '  '
        if layer:
            info += 'The following course(s) will not satisfy the requirements (' + course_set.name + '):\n'
        else:
            info += 'The following course(s) will not satisfy the track\'s requirements (' + course_set.name + '):\n'
    elif not course_set.parent_course_set and not course_set.size:
        for i in range(layer - 1):
            info += '  '
        if layer:
            info += 'The following course(s) will not satisfy the requirements (' + course_set.name + '):\n'
        else:
            info += 'The following course(s) will not satisfy the track\'s requirements (' + course_set.name + '):\n'
    elif course_set.size:
        for i in range(layer - 1):
            info += '  '
        if course_set.limiter:
            info += 'At most ' + str(course_set.size) + ' course(s) from ' + course_set.name + ':\n'
        else:
            info += str(course_set.size) + ' course(s) from ' + course_set.name + ':\n'
    # all this section does is create the sentences before each set of courses

    # this is where courses get listed out, along with their properties
    for course in CourseInTrackSet.objects.filter(course_set=course_set):
        for i in range(layer):
            info += '  '
        if course.how_many_semesters > 1:
            info += str(course) + ', taken at least ' + str(course.how_many_semesters) + ' times.\n'
        elif course.each_semester:
            info += str(course) + '[required each semester]\n'
        else:
            info += str(course) + '\n'
    # this is where courses get listed out, along with their properties

    # this prints out course ranges (CSE500-CSE560)
    if course_set.lower_limit != 100 and course_set.upper_limit != 999 and course_set.department_limit != 'N/A':
        for i in range(layer - 1):
            info += '  '
        info += course_set.department_limit + str(course_set.lower_limit) + '-' + course_set.department_limit + str(
            course_set.upper_limit)
    # this prints out course ranges (CSE500-CSE560)

    # this is the recursion call
    for nested_set in TrackCourseSet.objects.filter(parent_course_set=course_set):
        info = display_set_info(nested_set, layer + 1, info)

    return info + '\n'


def display_track_info(track):
    info = 'All of the following areas must be fulfilled or adhered to, for a total of ' + str(
        track.minimum_credits_required) + ' credits and a GPA of at least ' + str(track.required_gpa) + ':\n\n'
    for course_set in TrackCourseSet.objects.filter(track=track, parent_course_set=None):
        info = display_set_info(course_set, 0, info)
    return info


def wrap_text(text, limit):
    # wraps text around the characters-per-line limit without fragmenting any words
    counter = 0
    text_list = list(text)
    for i in range(len(text_list)):
        if text_list[i] == '\n':
            counter = 0
        elif counter == limit:
            position = i
            while text_list[position] != ' ' and text_list[position] != '\n':
                position -= 1
            text_list[position] = '\n'
            counter = 0
        else:
            counter += 1

    return ''.join(text_list)


def major_index(request):
    class TrackInfo():
        def __init__(self, name, key, value):
            self.name = name
            self.key = key
            self.value = value

    track_info = [
        TrackInfo(track.name, str(track.major_id) + '_' + str(track.id), wrap_text(display_track_info(track), 80)) for
        track in
        Track.objects.all()]

    context = {'major_list': Major.objects.order_by('name')[1:],
               'track_list': Track.objects.all(),
               'track_course_sets': TrackCourseSet.objects.all(),
               'courses_in_sets': CourseInTrackSet.objects.all(),
               'course_relations': CourseToCourseRelation.objects.all(),
               'course_list': Course.objects.all(),
               'track_info_list': track_info}
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


def student_degree_reqs_loop(taken_courses, course_set, layer, info):
    # all this section does is create the sentences before each set of courses
    if course_set.parent_course_set and course_set.parent_course_set.size and not course_set.size:
        return info
    elif not course_set.parent_course_set and not course_set.size:
        return info
    elif course_set.size:
        for i in range(layer - 1):
            info += '  '
        if course_set.limiter:
            info += 'At most ' + str(course_set.size) + ' course(s) from ' + course_set.name + ':\n'
        else:
            info += str(course_set.size) + ' course(s) from ' + course_set.name + ':\n'
    # all this section does is create the sentences before each set of courses

    # this is where courses get listed out, along with their properties
    for course in CourseInTrackSet.objects.filter(course_set=course_set):
        taken_course_lookup = [i for i in taken_courses if i.course.course == course]
        taken = '' if not len(taken_course_lookup) else '[TAKEN]'
        for i in range(layer):
            info += '  '
        if course.how_many_semesters > 1:
            info += str(course) + ', taken at least ' + str(course.how_many_semesters) + ' times.\n'
        elif course.each_semester:
            info += str(course) + '[required each semester] [TAKEN ' + str(len(taken_course_lookup)) + ' TIMES]\n'
        else:
            info += str(course) + ' ' + taken + '\n'
    # this is where courses get listed out, along with their properties

    # this prints out course ranges (CSE500-CSE560)
    if course_set.lower_limit != 100 and course_set.upper_limit != 999 and course_set.department_limit != 'N/A':
        for i in range(layer - 1):
            info += '  '
        info += course_set.department_limit + str(course_set.lower_limit) + '-' + course_set.department_limit + str(
            course_set.upper_limit)
    # this prints out course ranges (CSE500-CSE560)

    # this is the recursion call
    for nested_set in TrackCourseSet.objects.filter(parent_course_set=course_set):
        info = student_degree_reqs_loop(taken_courses, nested_set, layer + 1, info)

    return info + '\n'


def stringify_student_degree_reqs(student):
    student_credits = 0
    transfer_credits = 0
    taken_courses = CoursesTakenByStudent.objects.filter(student=student)
    for i in taken_courses:
        if i.status == 'Passed':
            student_credits += i.credits_taken
        elif i.status == 'Transfer':
            transfer_credits += i.credits_taken
    if transfer_credits > 12:
        transfer_credits = 12
    total_credits = student_credits + transfer_credits

    info = 'All of the following areas must be fulfilled or adhered to, for a total of (' + str(
        total_credits) + '/' + str(student.track.minimum_credits_required) + ') credits and a GPA of at least ' + str(student.track.required_gpa) + ':\n\n'

    for course_set in TrackCourseSet.objects.filter(track=student.track, parent_course_set=None):
        info = student_degree_reqs_loop(taken_courses, course_set, 0, info)

    return info


def detail(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    comment_list = Comment.objects.filter(student=sbu_id)
    semester_list = {i.course.semester: 1 for i in StudentCourseSchedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sorted(semester_list, key=operator.attrgetter('year'))
    if student.track:
        degree_requirements_string = wrap_text(stringify_student_degree_reqs(student), 60)
    else:
        degree_requirements_string = "No track."
    return render(request, 'mast/detail.html', {'student': student,
                                                'major_list': Major.objects.order_by('name'),
                                                'classes_taken': CoursesTakenByStudent.objects.filter(student=student),
                                                'comment_list': comment_list.order_by('post_date'),
                                                'semester_list': semester_list,
                                                'schedule': StudentCourseSchedule.objects.filter(student=sbu_id),
                                                'requirements': degree_requirements_string
                                                })


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
