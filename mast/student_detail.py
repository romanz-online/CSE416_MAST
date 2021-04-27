import operator
from datetime import datetime

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Major, CoursesTakenByStudent, Comment, StudentCourseSchedule, TrackCourseSet, \
    CourseInTrackSet, CourseStatus


@login_required
def detail(request, sbu_id):
    is_student = False
    if request.user.groups.filter(name='Student'):
        is_student = True

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
                                                'is_student': is_student,
                                                'schedule': StudentCourseSchedule.objects.filter(student=sbu_id),
                                                'requirements': degree_requirements_string
                                                })


@login_required
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
    except:
        return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


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


def student_degree_reqs_loop(taken_courses, course_set, layer, info):
    # all this section does is create the sentences before each set of courses
    if course_set.parent_course_set and course_set.parent_course_set.size and not course_set.size:
        return info
    elif not course_set.parent_course_set and not course_set.size:
        return info
    elif course_set.size:
        # this is where courses get listed out, along with their properties
        for i in range(layer):
            info += '  '

        number_taken = 0

        if course_set.lower_limit != 100 and course_set.upper_limit != 999:
            taken_course_lookup = len([i for i in taken_courses if
                                       course_set.lower_limit <= i.course.course.number <= course_set.upper_limit if
                                       i.course.course.department == course_set.department_limit
                                       and (i.status == CourseStatus.PASSED or i.status == CourseStatus.TRANSFER)])
            if taken_course_lookup:
                number_taken += taken_course_lookup
                if course_set.leeway:
                    number_taken -= course_set.leeway // 3

        for track in TrackCourseSet.objects.filter(parent_course_set=course_set):
            if track.lower_limit != 100 and track.upper_limit != 999:
                taken_course_lookup = len(
                    [i for i in taken_courses if track.lower_limit <= i.course.course.number <= track.upper_limit
                     and i.course.course.department == track.department_limit
                     and (i.status == CourseStatus.PASSED or i.status == CourseStatus.TRANSFER)])
                number_taken += taken_course_lookup
                if course_set.limiter and taken_course_lookup:
                    if course_set.leeway:
                        number_taken -= course_set.leeway // 3
            else:
                for course in CourseInTrackSet.objects.filter(course_set=track):
                    taken_course_lookup = len([i for i in taken_courses if i.course.course == course.course
                                               and (
                                                           i.status == CourseStatus.PASSED or i.status == CourseStatus.TRANSFER)])
                    if course_set.limiter and taken_course_lookup >= track.size:
                        number_taken += track.size
                    else:
                        number_taken += taken_course_lookup

        if course_set.limiter:
            for course in CourseInTrackSet.objects.filter(course_set=course_set):
                taken_course_lookup = sum([i.credits_taken for i in taken_courses if
                                           i.course.course == course.course
                                           and (i.status == CourseStatus.PASSED or i.status == CourseStatus.TRANSFER)])
                number_taken += taken_course_lookup

            if course_set.lower_credit_limit != 0:
                info += str(course_set.lower_credit_limit) + '-' + str(course_set.size) + ' [' + str(
                    course_set.size) + ' current] applied credit(s) from ' + course_set.name
            else:
                info += 'At most (' + str(number_taken * 3) + '/' + str(
                    course_set.size) + ') credit(s) from ' + course_set.name

            if number_taken * 3 >= course_set.size:
                info += ' [CAPPED]'

            info += ':\n'
        else:
            for course in CourseInTrackSet.objects.filter(course_set=course_set):
                taken_course_lookup = len(
                    [i for i in taken_courses if i.course.course == course.course and (
                            i.status == CourseStatus.PASSED or i.status == CourseStatus.TRANSFER)])
                number_taken += taken_course_lookup
            if 'Elective' in course_set.name:
                info += str(course_set.size * 3) + ' credit(s) from ' + course_set.name + '.\n'
            else:
                info += '(' + str(number_taken) + '/' + str(course_set.size) + ') course(s) from ' + course_set.name
                if number_taken >= course_set.size:
                    info += ' [COMPLETED]'
                info += ':\n'

    # this is where courses get listed out, along with their properties
    for course in CourseInTrackSet.objects.filter(course_set=course_set):
        if course_set.lower_limit != 100 and course_set.upper_limit != 999:
            taken_course_lookup = [i for i in taken_courses if
                                   course_set.lower_limit <= i.course.course.number <= course_set.upper_limit
                                   and i.course.course.department == course_set.department_limit
                                   and i.status != CourseStatus.FAILED]
        else:
            taken_course_lookup = [i for i in taken_courses if i.course.course == course.course
                                   and i.status != CourseStatus.FAILED]
        flag = ''
        taken_count = 0
        pending_count = 0
        for i in taken_course_lookup:
            if i.status == CourseStatus.PASSED or i.status == CourseStatus.TRANSFER:
                taken_count += 1
            elif i.status == CourseStatus.PENDING:
                pending_count += 1

        if taken_count > 0 and pending_count == 0:
            flag = '[TAKEN]'
        elif pending_count > 0 and taken_count == 0:
            flag = '[PENDING]'
        elif pending_count > 0 and taken_count > 0:
            if course_set.limiter:
                flag = '[PENDING]'
            else:
                flag = '[TAKEN]'

        for i in range(layer + 1):
            info += '  '

        if course.how_many_semesters > 1:
            info += str(course) + ', taken at least ' + str(course.how_many_semesters) + ' times.'
            if taken_course_lookup:
                info += ' [' + str(taken_count) + ' TAKEN | ' + str(pending_count) + ' PENDING]'
        elif course.each_semester:
            info += str(course) + ' [required each semester]'
            if taken_course_lookup:
                info += ' [' + str(taken_count) + ' TAKEN | ' + str(pending_count) + ' PENDING]'
        else:
            info += str(course) + ' ' + flag

        info += '\n'

    number_taken = 0
    pending_count = 0
    taken_count = 0
    flag = ''
    if course_set.lower_limit != 100 and course_set.upper_limit != 999:
        taken_course_lookup = [i for i in taken_courses if
                               course_set.lower_limit <= i.course.course.number <= course_set.upper_limit
                               and i.course.course.department == course_set.department_limit
                               and i.status != CourseStatus.FAILED]
        if taken_course_lookup:
            number_taken += len(taken_course_lookup)
            if course_set.limiter:
                number_taken -= course_set.leeway // 3
            for i in taken_course_lookup:
                if i.status == CourseStatus.PASSED or i.status == CourseStatus.TRANSFER:
                    taken_count += 1
                elif i.status == CourseStatus.PENDING:
                    pending_count += 1
    for track in TrackCourseSet.objects.filter(parent_course_set=course_set):
        if track.lower_limit != 100 and track.upper_limit != 999:
            taken_course_lookup = [i for i in taken_courses if
                                   track.lower_limit <= i.course.course.number <= track.upper_limit
                                   and i.course.course.department == track.department_limit
                                   and i.status != CourseStatus.FAILED]
            if taken_course_lookup:
                number_taken += len(taken_course_lookup)
                if track.limiter:
                    number_taken -= track.leeway // 3
                for i in taken_course_lookup:
                    if i.status == CourseStatus.PASSED or i.status == CourseStatus.TRANSFER:
                        taken_count += 1
                    elif i.status == CourseStatus.PENDING:
                        pending_count += 1

    if taken_count > 0 and pending_count == 0:
        flag = '[TAKEN]'
    elif pending_count > 0 and taken_count == 0:
        flag = '[PENDING]'
    elif pending_count > 0 and taken_count > 0:
        if course_set.limiter:
            flag = '[PENDING]'
        else:
            flag = '[TAKEN]'

    if number_taken <= 0:
        flag = ''

    # this prints out course ranges (CSE500-CSE560)
    if course_set.lower_limit != 100 and course_set.upper_limit != 999 and course_set.department_limit != 'N/A':
        for i in range(layer + 1):
            info += '  '
        info += course_set.department_limit + str(course_set.lower_limit) + '-' + course_set.department_limit + str(
            course_set.upper_limit) + ' ' + flag + '\n'

    # this is the recursion call
    for nested_set in TrackCourseSet.objects.filter(parent_course_set=course_set):
        info = student_degree_reqs_loop(taken_courses, nested_set, layer + 1, info)

    return info + '\n'


def stringify_student_degree_reqs(student):
    taken_courses = CoursesTakenByStudent.objects.filter(student=student)
    total_credits = student.credits_taken

    info = ''
    info += 'Satisfied Requirements: ' + str(student.satisfied_courses) + '\n'
    info += 'Pending Requirements: ' + str(student.pending_courses) + '\n'
    info += 'Unsatisfied Requirements: ' + str(student.unsatisfied_courses) + '\n'

    info += '\nAll of the following areas must be fulfilled or adhered to, for a total of (' + str(
        total_credits) + '/' + str(student.track.minimum_credits_required) + ') '
    if total_credits >= student.track.minimum_credits_required:
        info += '[COMPLETED] '

    info += 'credits and a GPA of at least ' + str(student.track.required_gpa) + ' [current GPA: ' + str(
        student.gpa) + ']'
    if student.gpa >= student.track.required_gpa:
        info += ' [COMPLETED]'

    info += ':\n\n'

    for course_set in TrackCourseSet.objects.filter(track=student.track, parent_course_set=None):
        info = student_degree_reqs_loop(taken_courses, course_set, 0, info)

    return info
