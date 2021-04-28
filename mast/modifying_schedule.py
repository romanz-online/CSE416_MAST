import operator

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Course, CourseInstance, CoursesTakenByStudent, Grade, StudentCourseSchedule, Semester, \
    Season, ScheduleStatus

from . import editing_student


@login_required
def edit_schedule(request, sbu_id):
    """
    Retrieves and renders a specific student's schedule to be edited on their respective page.
    
        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 
            sbu_id (int): The SBU ID used to retrieve the student object. 

        Returns:
            render (HttpResponse): Returns the respective view containing the respective information of the student schedule retrieved.     
    """

    # retrieve requested student, their grades, and the semesters they have taken classes in
    student = get_object_or_404(Student, pk=sbu_id)
    grade_list = [i[0] for i in Grade.choices]

    semester_list = {i.course.semester: 1 for i in
                     StudentCourseSchedule.objects.filter(student=sbu_id, schedule_id=0)}.keys()
    semester_list = sort_semester_list(semester_list)

    # render classes and grades in order of semester taken
    return render(request, 'mast/edit_schedule.html', {'student': student,
                                                       'grade_list': grade_list,
                                                       'course_list': CourseInstance.objects.all(),
                                                       'classes_taken': CoursesTakenByStudent.objects.all(),
                                                       'semester_list': semester_list,
                                                       'schedule': StudentCourseSchedule.objects.filter(student=sbu_id,
                                                                                                        schedule_id=0)
                                                       })


@login_required
def add_scheduled_semester(request, sbu_id):
    """
    Adds a scheduled semester to the student list.
    
        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 
            sbu_id (int): The SBU ID used to retrieve the student object. 

        Returns:
            render (HttpResponse): Returns the respective view containing the respective information of the student schedule retrieved.     
    """
    # retrieve requested student, their grades, the current semester, and the semesters they have taken clases in
    student = get_object_or_404(Student, pk=sbu_id)
    grade_list = [i[0] for i in Grade.choices]
    current_semester = Semester.objects.get(is_current_semester=True)
    semester_list = {i.course.semester: 1 for i in StudentCourseSchedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sort_semester_list(semester_list)
    # if the semester list is not empty, find the next chronological semester after the latest currently in schedule
    if semester_list:
        full_semester_list = [i for i in Semester.objects.all()]
        full_semester_list = sort_semester_list(full_semester_list)

        # retrieve index of latest semester currently in student's schedule
        i = full_semester_list.index(semester_list[len(semester_list) - 1])
        # if next semester to be added is not in fulle semester list
        if i + 1 >= len(full_semester_list):
            return edit_schedule()
        # retrieve and append next chronological semester to student schedule
        s = full_semester_list[i + 1]
        semester_list.append(s)
    # else append current semester as the first semester
    else:
        semester_list.append(current_semester)
        s = current_semester

    # if there is no empty course instance in the database yet, create one, so that only one instance of an exmpty course exists
    if not Course.objects.filter(name='', department='', number=0):
        c = Course(name='', department='', number=0)
        c.save()
    c = Course.objects.filter(name='', department='', number=0)[0]
    if not CourseInstance.objects.filter(course=c, section=999, semester=s):
        i = CourseInstance(course=c, section=999, semester=s)
        i.save()

    # add an empty corurse instance to schdeuled semester, to save semester in student schedule in database
    empty_course = CourseInstance.objects.filter(semester=s, section=999)[0]
    empty_course.save()
    empty_schedule_course = StudentCourseSchedule(student=student, course=empty_course)
    empty_schedule_course.save()
    return edit_schedule(request, sbu_id)


def sort_semester_list(semester_list):
    """
    Sorts a list of semesters into chronological order
    
        Parameters: 
            semester_list [Semester]: A list of unsorted semester objects.

        Returns:
            sorted_semester_list [Semester]: The sorted list of semester objects.
    """
    new_list = []
    index = 0
    placed = False
    enum = {Season.WINTER: 0, Season.SPRING: 1, Season.SUMMER: 2, Season.FALL: 3}

    for semester in semester_list:
        # if the new_list is still empty, simply place the semester
        if not new_list:
            new_list.append(semester)
        # otherwise append to correct orderted index
        else:
            for i in new_list:
                if not placed:
                    if i.year > semester.year:
                        new_list.insert(index - 1, semester)
                        placed = True
                    index += 1
            if not placed:
                new_list.append(semester)
        index = 0

    restart = True
    while restart:
        restart = False
        for i in range(len(new_list) - 1):
            if enum[new_list[i].season] > enum[new_list[i + 1].season] and new_list[i].year == new_list[i + 1].year:
                new_list[i], new_list[i + 1] = new_list[i + 1], new_list[i]
                restart = True

    return sorted(new_list, key=operator.attrgetter('year'))


@login_required
def approve_all(request, sbu_id):
    for i in StudentCourseSchedule.objects.filter(student=sbu_id, schedule_id=0):
        i.status = ScheduleStatus.APPROVED
        i.save()

    return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))


@login_required
def add_scheduled_course(request, sbu_id):
    """
    Adds a scheduled course to the student schedule.
    
        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 
            sbu_id (int): The SBU ID used to retrieve the student object. 

        Returns:
            render (HttpResponse): Returns the respective view containing the respective information of the student schedule retrieved.     
    """
    student = get_object_or_404(Student, pk=sbu_id)
    # retrieve selected course and add to student's schedule in database
    try:
        new_course = request.GET['course']
        new_course = CourseInstance.objects.get(id=new_course)
        c = StudentCourseSchedule(student=student, course=new_course)
        c.save()
        editing_student.sync_course_data(student)
    except:
        return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))


@login_required
def modify_scheduled_course(request, sbu_id, course):
    """
    Removes a scheduled course from the student schedule.
    
        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 
            sbu_id (int): The SBU ID used to retrieve the student object. 

        Returns:
            render (HttpResponse): Returns the respective view containing the respective information of the student schedule retrieved.     
    """
    # retrieve selected course and remove it from student's schedule in database
    student = get_object_or_404(Student, pk=sbu_id)
    course_record = get_object_or_404(CourseInstance, pk=course)
    try:
        c = StudentCourseSchedule.objects.get(student=student, course=course_record)
        if request.GET['action'] == 'approve':
            c.status = ScheduleStatus.APPROVED
            c.save()
        elif request.GET['action'] == 'remove':
            c.delete()
            editing_student.sync_course_data(student)
        else:
            raise Exception()
    except:
        return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))
