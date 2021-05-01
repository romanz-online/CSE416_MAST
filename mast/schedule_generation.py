from django.shortcuts import get_object_or_404, render

from .models import Student, Course, CourseInstance, CoursePrerequisiteSet, Prerequisite, StudentCourseSchedule, \
    Semester


def schedule_generation(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    course_list = {i for i in CourseInstance.objects.all() if i.section != 999}
    context = {
        'student': student,
        'course_list': course_list
    }
    return render(request, 'mast/schedule_generation.html', context)


def generate_schedule(request, sbu_id):
    preference = request.POST['preference0']
    count = 0
    preferences = {}
    while preference:
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
        key = 'preference' + str(count)
        try:
            preference = request.POST[key]
        except:
            preference = None

    # values and their meanings:
    # 0 - no preference. ignore it
    # 1 - highest preference
    # 2 - second highest preference
    # 3 - third highest preference
    # 4 - don't offer this specific section (AKA don't offer this CourseInstance)
    # 5 - don't offer this course at all (AKA don't offer the corresponding Course)

    # do stuff with the "preferences" dictionary here

    student = get_object_or_404(Student, pk=sbu_id)
    context = {
        'student': student
    }
    return render(request, 'mast/offered_schedules.html', context)


def offered_schedules(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    context = {
        'student': student
    }
    return render(request, 'mast/offered_schedules.html', context)


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
