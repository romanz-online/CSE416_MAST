import operator
from enum import Enum

from django.shortcuts import render
from .models import Student, Major, Semester, Track, Department

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


class MajorTrack:
    def __init__(self, major, track, id):
        self.major = major
        self.track = track
        self.id = id


def student_index(request):
    global current_search, sorted_by
    if not Major.objects.filter(department=Department.NONE):
        semester = Semester.objects.all()[0]
        none_major = Major(department=Department.NONE,
                           name='(None)',
                           requirement_semester=semester)
        none_major.save()
    major_track_list = []
    for m in Major.objects.all():
        for t in Track.objects.all():
            if t.major == m:
                major_track_list.append(MajorTrack(m.name, t.name, t.id))
    context = {'student_list': Student.objects.order_by('sbu_id'),
               'major_list': Major.objects.order_by('name'),
               'semesters': Semester.objects.all(),
               'requirement_semesters': Semester.objects.all(),
               'major_track_list': major_track_list}
    current_search['student_list'] = Student.objects.order_by('sbu_id')
    current_search['major_list'] = Major.objects.order_by('name')
    sorted_by = SortedBy.NONE
    return render(request, 'mast/student_index.html', context)


def delete_all_students(request):
    global current_search, sorted_by

    for student in Student.objects.all():
        student.delete()

    context = {'student_list': Student.objects.order_by('sbu_id'),
               'major_list': Major.objects.order_by('name'),
               'semesters': Semester.objects.all(),
               'requirement_semesters': Semester.objects.all()}
    current_search['student_list'] = Student.objects.order_by('sbu_id')
    current_search['major_list'] = Major.objects.order_by('name')
    sorted_by = SortedBy.NONE
    return render(request, 'mast/student_index.html', context)


def search(request):
    global current_search
    name_search = request.GET['name']
    sbu_id_search = request.GET['sbu_id']
    major_search = request.GET['major']
    graduated_search = request.GET['graduated']
    withdrew_search = request.GET['withdrew']
    plan_complete_search = request.GET['plan_complete']
    plan_valid_search = request.GET['plan_valid']
    first_name_list = Student.objects.filter(first_name__icontains=name_search)
    last_name_list = Student.objects.filter(last_name__icontains=name_search)
    sbu_id_list = Student.objects.filter(sbu_id__icontains=sbu_id_search)

    if graduated_search == 0:
        first_name_list = first_name_list.filter(graduated=True)
        last_name_list = last_name_list.filter(graduated=True)
        sbu_id_list = sbu_id_list.filter(graduated=True)
    elif graduated_search == 1:
        first_name_list = first_name_list.filter(graduated=False)
        last_name_list = last_name_list.filter(graduated=False)
        sbu_id_list = sbu_id_list.filter(graduated=False)

    if withdrew_search == 0:
        first_name_list = first_name_list.filter(withdrew=True)
        last_name_list = last_name_list.filter(withdrew=True)
        sbu_id_list = sbu_id_list.filter(withdrew=True)
    elif withdrew_search == 1:
        first_name_list = first_name_list.filter(withdrew=False)
        last_name_list = last_name_list.filter(withdrew=False)
        sbu_id_list = sbu_id_list.filter(withdrew=False)

    if plan_complete_search == 0:
        first_name_list = first_name_list.filter(schedule_completed=True)
        last_name_list = last_name_list.filter(schedule_completed=True)
        sbu_id_list = sbu_id_list.filter(schedule_completed=True)
    elif plan_complete_search == 1:
        first_name_list = first_name_list.filter(schedule_completed=False)
        last_name_list = last_name_list.filter(schedule_completed=False)
        sbu_id_list = sbu_id_list.filter(schedule_completed=False)

    if plan_valid_search == 0:
        first_name_list = first_name_list.filter(valid_schedule=True)
        last_name_list = last_name_list.filter(valid_schedule=True)
        sbu_id_list = sbu_id_list.filter(valid_schedule=True)
    elif plan_valid_search == 1:
        first_name_list = first_name_list.filter(valid_schedule=False)
        last_name_list = last_name_list.filter(valid_schedule=False)
        sbu_id_list = sbu_id_list.filter(valid_schedule=False)

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
               'major_search': int(major_search),
               'plan_complete_search': plan_complete_search,
               'plan_valid_search': plan_valid_search
               }

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
