import operator

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Course, CourseInstance, CoursesTakenByStudent, Grade, StudentCourseSchedule, Semester, \
    Season

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
    student = get_object_or_404(Student, pk=sbu_id)
    grade_list = [i[0] for i in Grade.choices]
    semester_list = {i.course.semester: 1 for i in StudentCourseSchedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sort_semester_list(semester_list)
    return render(request, 'mast/edit_schedule.html', {'student': student,
                                                       'grade_list': grade_list,
                                                       'course_list': CourseInstance.objects.all(),
                                                       'classes_taken': CoursesTakenByStudent.objects.all(),
                                                       'semester_list': semester_list,
                                                       'schedule': StudentCourseSchedule.objects.filter(
                                                           student=sbu_id)
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
    student = get_object_or_404(Student, pk=sbu_id)
    grade_list = [i[0] for i in Grade.choices]
    current_semester = Semester.objects.get(is_current_semester=True)
    semester_list = {i.course.semester: 1 for i in StudentCourseSchedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sort_semester_list(semester_list)
    if semester_list:
        full_semester_list = [i for i in Semester.objects.all()]
        full_semester_list = sort_semester_list(full_semester_list)
        i = full_semester_list.index(semester_list[0])
        while full_semester_list[i] in semester_list:
            i += 1
        if i > len(full_semester_list):
            return render(request, 'mast/edit_schedule.html', {'student': student,
                                                               'grade_list': grade_list,
                                                               'course_list': CourseInstance.objects.all(),
                                                               'classes_taken': CoursesTakenByStudent.objects.all(),
                                                               'semester_list': semester_list,
                                                               'schedule': StudentCourseSchedule.objects.filter(
                                                                   student=sbu_id)
                                                               })
        s = full_semester_list[i]
        semester_list.append(s)
        if not Course.objects.filter(name='', department='', number=0):
            c = Course(name='', department='', number=0)
            c.save()
        c = Course.objects.filter(name='', department='', number=0)[0]
        if not CourseInstance.objects.filter(course=c, section=999, semester=s):
            i = CourseInstance(course=c, section=999, semester=s)
            i.save()
        empty_course = CourseInstance.objects.get(semester=s, section=999)
        empty_course.save()
        empty_schedule_course = StudentCourseSchedule(student=student, course=empty_course)
        empty_schedule_course.save()
    else:
        semester_list.append(current_semester)
        if not Course.objects.filter(name='', department='', number=0):
            c = Course(name='', department='', number=0)
            c.save()
        c = Course.objects.filter(name='', department='', number=0)[0]
        if not CourseInstance.objects.filter(course=c, section=999, semester=current_semester):
            i = CourseInstance(course=c, section=999, semester=current_semester)
            i.save()
        empty_course = CourseInstance.objects.get(semester=current_semester, section=999)
        empty_course.save()
        empty_schedule_course = StudentCourseSchedule(student=student, course=empty_course)
        empty_schedule_course.save()
    return render(request, 'mast/edit_schedule.html', {'student': student,
                                                       'grade_list': grade_list,
                                                       'course_list': CourseInstance.objects.all(),
                                                       'classes_taken': CoursesTakenByStudent.objects.all(),
                                                       'semester_list': semester_list,
                                                       'schedule': StudentCourseSchedule.objects.filter(
                                                           student=sbu_id)
                                                       })


def sort_semester_list(semester_list):
    new_list = []
    index = 0
    placed = False
    enum = {Season.WINTER: 0, Season.SPRING: 1, Season.SUMMER: 2, Season.FALL: 3}

    for semester in semester_list:
        if not new_list:
            new_list.append(semester)
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
        for i in range(len(new_list)-1):
            if enum[new_list[i].season] > enum[new_list[i+1].season] and new_list[i].year == new_list[i+1].year:
                new_list[i], new_list[i+1] = new_list[i+1], new_list[i]
                restart = True

    return sorted(new_list, key=operator.attrgetter('year'))


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
def remove_scheduled_course(request, sbu_id, course):
    """
    Removes a scheduled course from the student schedule.
    
        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 
            sbu_id (int): The SBU ID used to retrieve the student object. 

        Returns:
            render (HttpResponse): Returns the respective view containing the respective information of the student schedule retrieved.     
    """
    student = get_object_or_404(Student, pk=sbu_id)
    course_record = get_object_or_404(CourseInstance, pk=course)
    try:
        c = StudentCourseSchedule.objects.get(student=student, course=course_record)
        c.delete()
        editing_student.sync_course_data(student)
    except:
        return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))
