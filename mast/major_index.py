from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import Student, Major, Track, TrackCourseSet, CourseInTrackSet, CourseToCourseRelation, Course


@login_required
def major_index(request):
    is_student = False
    student = None
    if request.user.groups.filter(name='Student'):
        is_student = True
        sbu_id = request.user.username
        student = get_object_or_404(Student, pk=sbu_id)

    class TrackInfo:
        def __init__(self, name, key, value):
            self.name = name
            self.key = key
            self.value = value

    track_info = [
        TrackInfo(track.name, str(track.major_id) + '_' + str(track.id), wrap_text(display_track_info(track), 80)) for
        track in
        Track.objects.all()]

    major_list = [i for i in Major.objects.order_by('name') if i.name != '(None)']
    context = {'major_list': major_list,
               'track_list': Track.objects.all(),
               'track_course_sets': TrackCourseSet.objects.all(),
               'courses_in_sets': CourseInTrackSet.objects.all(),
               'course_relations': CourseToCourseRelation.objects.all(),
               'course_list': Course.objects.all(),
               'track_info_list': track_info,
               'is_student': is_student,
               'student': student,
               }
    return render(request, 'mast/major_index.html', context)


def display_set_info(course_set, layer, info):
    # all this section does is create the sentences before each set of courses
    if course_set.parent_course_set and course_set.parent_course_set.size and not course_set.size:
        for i in range(layer - 1):
            info += '  '
        if layer:
            info += 'The following course(s) will not satisfy the requirements (' + course_set.name + '):\n'
        else:
            info += 'The following course(s) will not satisfy the track\'s requirements (' + course_set.name + '):\n'
    elif not course_set.size:
        for i in range(layer - 1):
            info += '  '
        if layer:
            info += 'The following course(s) will not satisfy the requirements (' + course_set.name + '):\n'
        else:
            info += 'The following course(s) will not satisfy the track\'s requirements (' + course_set.name + '):\n'
    elif course_set.size:
        for i in range(layer - 1):
            info += '  '
        if "Elective" in course_set.name:
            info += str(course_set.size * 3) + " credit(s) from " + course_set.name + ".\n"
        else:
            if course_set.limiter:
                info += 'At most ' + str(course_set.size) + ' credit(s) from ' + course_set.name + ':\n'
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
        for i in range(layer):
            info += '  '
        info += course_set.department_limit + str(course_set.lower_limit) + '-' + course_set.department_limit + str(
            course_set.upper_limit) + '\n'
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
