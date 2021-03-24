from datetime import datetime
from enum import Enum
import operator

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Major, Course, Required_Classes_for_Track, Classes_Taken_by_Student, Grade, CourseStatus, \
    Comment, Student_Course_Schedule, Semester, Requirement_Semester, Season

global current_search
current_search = {'student_list': Student.objects.order_by('sbu_id'),
                  'major_list': Major.objects.order_by('name'),
                  'name_search': '',
                  'sbu_id_search': '',
                  'graduated_search': False,
                  'withdrew_search': False,
                  'major_search': 0}

class SortedBy(Enum):
    NONE = 0
    ID = 1
    NAME = 2
    GRADUATION = 3
    ATTENDANCE = 4
    ID_INV = 5
    NAME_INV = 6
    GRADUATION_INV = 7
    ATTENDANCE_INV = 8



global sorted_by
sorted_by = SortedBy.NONE

def home(request):
    return render(request, 'mast/home.html', {})


def gpd_landing(request):
    return render(request, 'mast/gpd_landing.html', {})


def major_index(request):
    context = {'major_list': Major.objects.order_by('name')[1:],
               'required_classes_for_major_list': Required_Classes_for_Track.objects.order_by('major')}
    return render(request, 'mast/major_index.html', context)


def add_student(request):
    context = {'major_list': Major.objects.order_by('name')[1:], 'semesters': Semester.objects.order_by('year'),
               'requirement_semesters': Requirement_Semester.objects.order_by('year')}
    return render(request, 'mast/new_student.html', context)


def commit_new_student(request):
    id_list = [i.sbu_id for i in Student.objects.all()]
    id_taken = False
    sbu_id = request.GET['sbu_id']
    first_name = request.GET['first_name']
    last_name = request.GET['last_name']
    email = request.GET['email']
    major = request.GET['major']
    entry_semester = request.GET['entry_semester']
    requirement_semester = request.GET['requirement_semester']
    try:
        if int(sbu_id) in id_list:
            id_taken = True
            raise Exception('non-unique id')
        student = Student(sbu_id=sbu_id,
                          first_name=first_name,
                          last_name=last_name,
                          email=email,
                          major=Major.objects.get(id=int(major)),
                          entry_semester=Semester.objects.get(id=int(entry_semester)),
                          requirement_semester=Requirement_Semester.objects.get(id=int(requirement_semester))
                          )
        student.save()
    except:
        if id_taken:
            return render(request, 'mast/new_student.html', {
                'major_list': Major.objects.order_by('name'),
                'error_message': "ID taken."
            })
        else:
            return render(request, 'mast/new_student.html', {
                'major_list': Major.objects.order_by('name'),
                'error_message': "Something went wrong."
            })
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


def student_index(request):
    global current_search, sorted_by
    context = {'student_list': Student.objects.order_by('sbu_id'), 'major_list': Major.objects.order_by('name')}
    current_search['student_list'] = Student.objects.order_by('sbu_id')
    current_search['major_list'] = Major.objects.order_by('name')
    sorted_by = SortedBy.NONE
    return render(request, 'mast/student_index.html', context)


def search(request):
    global current_search
    name_search = request.GET['name']
    sbu_id_search = request.GET['sbu_id']
    major_search = request.GET['major']
    graduated_search = True if request.GET['graduated'] == 'yes' else False
    withdrew_search = True if request.GET['withdrew'] == 'yes' else False
    first_name_list = Student.objects.filter(first_name__icontains=name_search)
    last_name_list = Student.objects.filter(last_name__icontains=name_search)
    sbu_id_list = Student.objects.filter(sbu_id__icontains=sbu_id_search)

    if not graduated_search:
        first_name_list = first_name_list.filter(graduated=False)
        last_name_list = last_name_list.filter(graduated=False)
        sbu_id_list = sbu_id_list.filter(graduated=False)
    if not withdrew_search:
        first_name_list = first_name_list.filter(withdrew=False)
        last_name_list = last_name_list.filter(withdrew=False)
        sbu_id_list = sbu_id_list.filter(withdrew=False)

    m = Major.objects.get(id=int(major_search))
    if m.name != '(None)':
        first_name_list = first_name_list.filter(major=m)
        last_name_list = last_name_list.filter(major=m)
        sbu_id_list = sbu_id_list.filter(major=m)

    name_list = set(first_name_list).union(set(last_name_list))
    student_list = list(set(name_list) & set(sbu_id_list))
    context = {'student_list': student_list,
               'major_list': Major.objects.order_by('name'),
               'name_search': name_search,
               'sbu_id_search': sbu_id_search,
               'graduated_search': graduated_search,
               'withdrew_search': withdrew_search,
               'major_search': int(major_search)}

    current_search = context
    return render(request, 'mast/student_index.html', context)


def sort_by_id(request):
    global current_search, sorted_by
    if sorted_by == SortedBy.ID:
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('sbu_id'), reverse=True)
        sorted_by = SortedBy.ID_INV
    else:
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('sbu_id'))
        sorted_by = SortedBy.ID
    context = current_search
    return render(request, 'mast/student_index.html', context)


def sort_by_name(request):
    global current_search, sorted_by
    if sorted_by == SortedBy.NAME:
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('last_name'), reverse=True)
        sorted_by = SortedBy.NAME_INV
    else:
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('last_name'))
        sorted_by = SortedBy.NAME
    context = current_search
    return render(request, 'mast/student_index.html', context)


def sort_by_graduation(request):
    global current_search, sorted_by
    if sorted_by == SortedBy.GRADUATION:
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('graduation_season'))
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('graduation_year'), reverse=True)
        sorted_by = SortedBy.GRADUATION_INV
    else:
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('graduation_season'), reverse=True)
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('graduation_year'))
        sorted_by = SortedBy.GRADUATION
    context = current_search
    return render(request, 'mast/student_index.html', context)


def sort_by_attendance(request):
    global current_search, sorted_by
    if sorted_by == SortedBy.ATTENDANCE:
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('unsatisfied_courses'), reverse=True)
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('pending_courses'), reverse=True)
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('satisfied_courses'), reverse=True)
        sorted_by = SortedBy.ATTENDANCE_INV
    else:
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('unsatisfied_courses'))
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('pending_courses'))
        current_search['student_list'] = sorted(current_search['student_list'],
                                                key=operator.attrgetter('satisfied_courses'))
        sorted_by = SortedBy.ATTENDANCE
    context = current_search
    return render(request, 'mast/student_index.html', context)


def detail(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    comment_list = Comment.objects.filter(student=sbu_id)
    semester_list = {i.course.semester:1 for i in Student_Course_Schedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sorted(semester_list, key=operator.attrgetter('year'))
    return render(request, 'mast/detail.html', {'student': student,
                                                'major_list': Major.objects.order_by('name'),
                                                'classes_taken': Classes_Taken_by_Student.objects.all(),
                                                'comment_list': comment_list.order_by('post_date'),
                                                'semester_list': semester_list,
                                                'schedule': Student_Course_Schedule.objects.filter(student=sbu_id)
                                                })


def edit_schedule(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    grade_list = [i[0] for i in Grade.choices]
    semester_list = {i.course.semester:1 for i in Student_Course_Schedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sorted(semester_list, key=operator.attrgetter('year'))
    return render(request, 'mast/edit_schedule.html', {'student': student,
                                                       'grade_list': grade_list,
                                                       'course_list': Course.objects.order_by('department'),
                                                       'classes_taken': Classes_Taken_by_Student.objects.all(),
                                                       'semester_list': semester_list,
                                                       'schedule': Student_Course_Schedule.objects.filter(student=sbu_id)
                                                       })


def add_scheduled_semester(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    grade_list = [i[0] for i in Grade.choices]
    current_semester = Semester.objects.get(is_current_semester=True)
    semester_list = {i.course.semester:1 for i in Student_Course_Schedule.objects.filter(student=sbu_id)}.keys()
    semester_list = sorted(semester_list, key=operator.attrgetter('year'))
    if semester_list:
        full_semester_list = [i for i in Semester.objects.all()]
        full_semester_list = sorted(full_semester_list, reverse=True, key=operator.attrgetter('season'))
        full_semester_list = sorted(full_semester_list, key=operator.attrgetter('year'))
        i = full_semester_list.index(semester_list[0])
        while full_semester_list[i] in semester_list:
            i += 1
        semester_list.append(full_semester_list[i])
        empty_course = Course(name='', department='', number=0, semester=full_semester_list[i], section=0, timeslot=datetime.now())
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
                                                       'schedule': Student_Course_Schedule.objects.filter(student=sbu_id)
                                                       })


def add_scheduled_course(request, sbu_id):
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
    student = get_object_or_404(Student, pk=sbu_id)
    course_record = get_object_or_404(Course, pk=course)
    try:
        c = Student_Course_Schedule.objects.get(student=student, course=course_record)
        c.delete()
    except:
        return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit_schedule', args=(sbu_id,)))


def add_comment(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        new_comment = request.GET['new_comment']
        if new_comment == '':
            raise Exception
        c = Comment(student=student, text=str(new_comment), post_date=str(datetime.now()))
        c.save()
    except:
        return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


def edit(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    grade_list = [i[0] for i in Grade.choices]
    course_status_list = [i[0] for i in CourseStatus.choices]
    return render(request, 'mast/edit.html', {'student': student,
                                              'major_list': Major.objects.order_by('name'),
                                              'course_list': Course.objects.order_by('name'),
                                              'classes_taken': Classes_Taken_by_Student.objects.all(),
                                              'grade_list': grade_list,
                                              'course_status_list': course_status_list,
                                              'semesters': Semester.objects.order_by('year'),
                                              'requirement_semesters': Requirement_Semester.objects.order_by('year')})


def commit_edit(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        first_name = request.GET['first_name']
        last_name = request.GET['last_name']
        email = request.GET['email']
        major = request.GET['major']
        graduated = True if request.GET['graduated'] == 'yes' else False
        withdrew = True if request.GET['withdrew'] == 'yes' else False
        entry_semester = request.GET['entry_semester']
        requirement_semester = request.GET['requirement_semester']

        student.first_name = first_name
        student.last_name = last_name
        student.email = email
        student.major = Major.objects.get(id=int(major))
        student.graduated = graduated
        student.withdrew = withdrew
        student.entry_semester=Semester.objects.get(id=int(entry_semester))
        student.requirement_semester=Requirement_Semester.objects.get(id=int(requirement_semester))
        if student.graduated:
            graduation_semester = request.GET['graduation_semester']
            graduation_semester = Semester.objects.get(id=int(graduation_semester))
            student.graduation_season = graduation_semester.season
            student.graduation_year = graduation_semester.year
        else:
            student.graduation_season = Season.NOT_APPLICABLE
            student.graduation_year = 0

        for course in Classes_Taken_by_Student.objects.all():
            if course.student == student and course.status != 'Pending':
                new_grade = request.GET[str(course.id)]
                new_status = request.GET[str(course.id) + 'status']
                if course.grade != new_grade:
                    course.grade = new_grade
                if course.status != new_status:
                    course.status = new_status
                course.save()

        sum = 0
        total = 0
        for course in Classes_Taken_by_Student.objects.all():
            if course.student == student and course.status != 'Pending':
                if course.grade not in ['W', 'S', 'U', 'I', 'N/A']:
                    sum += get_grade_number(course.grade)
                    total += 1
        if total == 0:
            total = 1
        sum = sum / total
        student.gpa = format(sum, '.2f')

        student.save()
    except:
        student = get_object_or_404(Student, pk=sbu_id)
        grade_list = [i[0] for i in Grade.choices]
        course_status_list = [i[0] for i in CourseStatus.choices]
        return render(request, 'mast/edit.html', {'student': student,
                                                  'major_list': Major.objects.order_by('name'),
                                                  'course_list': Course.objects.order_by('name'),
                                                  'classes_taken': Classes_Taken_by_Student.objects.all(),
                                                  'grade_list': grade_list,
                                                  'course_status_list': course_status_list,
                                                  'semesters': Semester.objects.order_by('year'),
                                                  'requirement_semesters': Requirement_Semester.objects.order_by('year'),
                                                  'error_message': "Something went wrong."
                                                  })
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


def get_grade_number(grade):
    dict = {'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0,
            'D-': 0.7, 'F': 0.0, 'S': 4.0}
    return dict[grade]


def add_taken_course(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        new_course = request.GET['course']
        new_course = Course.objects.get(id=new_course)
        # new_grade = request.GET['grade']
        c = Classes_Taken_by_Student(student=student, course=new_course, grade='A')
        c.save()
    except:
        return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))


def modify_course_in_progress(request, sbu_id, record):
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        r = Classes_Taken_by_Student.objects.get(id=record)
        if request.GET['action'] == 'pass':
            r.status = CourseStatus.PASSED
            r.grade = 'A'
            r.save()
            student.save()
        elif request.GET['action'] == 'fail':
            r.status = CourseStatus.FAILED
            r.grade = 'F'
            r.save()
            student.save()
        elif request.GET['action'] == 'drop':
            r.delete()
            student.save()
        else:
            raise Exception()
    except:
        return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))
