from datetime import datetime
import operator

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Course, Classes_Taken_by_Student, Grade, Student_Course_Schedule, Semester


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
    semester_list = {i.course.semester: 1 for i in Student_Course_Schedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sorted(semester_list, key=operator.attrgetter('year'))
    return render(request, 'mast/edit_schedule.html', {'student': student,
                                                       'grade_list': grade_list,
                                                       'course_list': Course.objects.order_by('department'),
                                                       'classes_taken': Classes_Taken_by_Student.objects.all(),
                                                       'semester_list': semester_list,
                                                       'schedule': Student_Course_Schedule.objects.filter(
                                                           student=sbu_id)
                                                       })


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
    semester_list = {i.course.semester: 1 for i in Student_Course_Schedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sorted(semester_list, key=operator.attrgetter('year'))
    if semester_list:
        full_semester_list = [i for i in Semester.objects.all()]
        full_semester_list = sorted(full_semester_list, reverse=True, key=operator.attrgetter('season'))
        full_semester_list = sorted(full_semester_list, key=operator.attrgetter('year'))
        i = full_semester_list.index(semester_list[0])
        while full_semester_list[i] in semester_list:
            i += 1
        semester_list.append(full_semester_list[i])
        empty_course = Course(name='', department='', number=0, semester=full_semester_list[i], section=0,
                              timeslot=datetime.now())
    else:
        semester_list.append(current_semester)
        empty_course = Course(name='', department='', number=0, semester=current_semester, section=0,
                              timeslot=datetime.now())
    empty_course.save()
    empty_schedule_course = Student_Course_Schedule(student=student, course=empty_course)
    empty_schedule_course.save()
    return render(request, 'mast/edit_schedule.html', {'student': student,
                                                       'grade_list': grade_list,
                                                       'course_list': Course.objects.order_by('department'),
                                                       'classes_taken': Classes_Taken_by_Student.objects.all(),
                                                       'semester_list': semester_list,
                                                       'schedule': Student_Course_Schedule.objects.filter(
                                                           student=sbu_id)
                                                       })


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
        new_course = Course.objects.get(id=new_course)
        c = Student_Course_Schedule(student=student, course=new_course)
        c.save()
    except:
        return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))


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
    course_record = get_object_or_404(Course, pk=course)
    try:
        c = Student_Course_Schedule.objects.get(student=student, course=course_record)
        c.delete()
    except:
        return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))
