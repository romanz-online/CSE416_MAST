from django.shortcuts import get_object_or_404, render

from .modifying_schedule import sort_semester_list
from django.contrib.auth.decorators import login_required
from .models import Student, Course, CourseInstance, CoursePrerequisiteSet, Prerequisite, StudentCourseSchedule, \
    Semester, ScheduleType, ScheduleStatus
from .classic_suggest import classic_suggest
from .smart_suggest import smart_suggest_gen


@login_required
def schedule_generation(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    course_list = {i for i in CourseInstance.objects.all() if i.section != 999}
    context = {
        'student': student,
        'course_list': course_list
    }
    return render(request, 'mast/schedule_generation.html', context)


@login_required
def generate_schedule(request, sbu_id):
    print("classic suggest")
    print("hello world")
    preference = 1
    count = 0
    preferences = {}
    while preference:
        key = 'preference' + str(count)
        try:
            preference = request.POST[key]
        except:
            break

        course = preference[:-1]
        course_preference = preference[len(preference) - 1:len(preference)]

        course_department = course[0:3]
        course_number = course[3:6]
        course_section = course[7:8]
        course_semester = course[11:len(course)]

        course = Course.objects.filter(department=course_department, number=course_number)[0]
        if course_semester == 'None':
            course_instance = CourseInstance.objects.filter(course=course, section=course_section, semester=None)[0]
        else:
            course_semester_year = course_semester[len(course_semester) - 4:len(course_semester)]
            course_semester_season = course_semester[0:len(course_semester) - 5]
            course_semester = Semester.objects.filter(season=course_semester_season, year=course_semester_year)[0]
            course_instance = CourseInstance.objects.filter(course=course,
                                                            section=course_section, semester=course_semester)[0]

        preferences[course_instance] = course_preference
        count += 1

    try:
        start_time = request.POST['start_time']
        print(start_time)
    except:
        start_time = None
    if not start_time:
        start_time = None

    try:
        end_time = request.POST['end_time']
        print(end_time)
    except:
        end_time = None
    if not end_time:
        end_time = None

    try:
        courses_per_semester = request.POST['courses_per_semester']
    except:
        courses_per_semester = 6
    if not courses_per_semester:
        courses_per_semester = 6

    # values and their meanings:
    # 0 - no preference. ignore it
    # 1 - highest preference
    # 2 - second highest preference
    # 3 - third highest preference
    # 4 - don't offer this specific section (AKA don't offer this CourseInstance)
    # 5 - don't offer this course at all (AKA don't offer the corresponding Course)

    # do stuff with the "preferences" dictionary, start_time, end_time, and courses_per_semester here

    prefer_courses = [[], [], []]
    for courseInstance in preferences.keys():
        if preferences[courseInstance] in [1, 2, 3]:
            match_course = courseInstance.course
            prefer_courses[preferences[courseInstance] - 1].append(match_course)
    time_constraints = [start_time, end_time]
    graduation_semester = None
    avoid_courses = []
    student = Student.objects.filter(sbu_id=sbu_id).first()

    classic_suggest(student, prefer_courses, courses_per_semester, avoid_courses, time_constraints, graduation_semester)
    return offered_schedules(request, sbu_id)


@login_required
def smart_suggest(request, sbu_id):
    #student = Student.objects.filter(sbu_id=sbu_id).first()
    #smart_suggest_gen(student)
    return offered_schedules(request, sbu_id)


@login_required
def offered_schedules(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)

    class Pair:
        def __init__(self, schedule_id, schedule_type):
            self.schedule_id = schedule_id
            self.schedule_type = schedule_type

        def __str__(self):
            return 'Schedule ' + str(self.schedule_id) + ' [' + self.schedule_type + ']'

    schedules = [i for i in StudentCourseSchedule.objects.filter(student=student) if i.schedule_id > 0]
    schedule_ids = sorted({i.schedule_id for i in schedules})
    pairs = [Pair(i, StudentCourseSchedule.objects.filter(schedule_id=i)[0].schedule_type) for i in schedule_ids if
             StudentCourseSchedule.objects.filter(schedule_id=i)[0].schedule_type != ScheduleType.DEFAULT]
    context = {
        'student': student,
        'schedules': pairs
    }

    return render(request, 'mast/offered_schedules.html', context)


@login_required
def schedule_display(request, sbu_id, schedule_id):
    student = get_object_or_404(Student, pk=sbu_id)
    schedule = StudentCourseSchedule.objects.filter(student=student, schedule_id=schedule_id)
    semesters = {i.course.semester for i in schedule}
    semesters = sort_semester_list(semesters)
    context = {
        'student': student,
        'schedule': schedule,
        'schedule_id': schedule_id,
        'semesters': semesters
    }
    return render(request, 'mast/display_schedule.html', context)


@login_required
def approve_all(request, sbu_id, schedule_id):
    student = get_object_or_404(Student, pk=sbu_id)
    schedule = StudentCourseSchedule.objects.filter(student=student, schedule_id=schedule_id)

    for i in schedule:
        if i.status != ScheduleStatus.APPROVED:
            i.status = ScheduleStatus.APPROVED
            i.save()
            new_record = StudentCourseSchedule(student=student, course=i.course, schedule_id=0,
                                               status=ScheduleStatus.APPROVED)
            new_record.save()

    return schedule_display(request, sbu_id, schedule_id)


@login_required
def approve_scheduled_course(request, sbu_id, schedule_id, course_id):
    student = get_object_or_404(Student, pk=sbu_id)
    course_record = get_object_or_404(CourseInstance, pk=course_id)
    c = StudentCourseSchedule.objects.get(student=student, course=course_record, schedule_id=schedule_id)
    c.status = ScheduleStatus.APPROVED
    c.save()
    new_record = StudentCourseSchedule(student=student, course=course_record, schedule_id=0,
                                       status=ScheduleStatus.APPROVED)
    new_record.save()

    return schedule_display(request, sbu_id, schedule_id)


# returns boolean indicating if all class prereqs have been met in a given schedule or not
def prereqs_met(student, course, schedule_id):
    student_courses = StudentCourseSchedule.objects.filter(student=student,
                                                           schedule_id=schedule_id) | StudentCourseSchedule.objects.filter(
        student=student, schedule_id=0)
    prereq_set = CoursePrerequisiteSet.objects.filter(parent_course=course)
    for prereq in Prerequisite.objects.filter(course_set=prereq_set):
        if prereq not in student_courses:
            return False

    for nested_set in CoursePrerequisiteSet.objects.filter(parent_set=prereq_set):
        met = False
        for prereq in Prerequisite.objects.filter(course_set=nested_set):
            if prereq in student_courses:
                met = True
        if not met:
            return False

    return True
