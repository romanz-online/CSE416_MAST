from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Major, Course, Classes_Taken_by_Student, Grade, CourseStatus, Semester,\
    Requirement_Semester, Season


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


def delete_record(request, sbu_id):
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        student.delete()
    except:
        grade_list = [i[0] for i in Grade.choices]
        course_status_list = [i[0] for i in CourseStatus.choices]
        return render(request, 'mast/edit.html', {'student': student,
                                                  'major_list': Major.objects.order_by('name'),
                                                  'course_list': Course.objects.order_by('name'),
                                                  'classes_taken': Classes_Taken_by_Student.objects.all(),
                                                  'grade_list': grade_list,
                                                  'course_status_list': course_status_list,
                                                  'semesters': Semester.objects.order_by('year'),
                                                  'requirement_semesters': Requirement_Semester.objects.order_by(
                                                      'year'),
                                                  'error_message': "Something went wrong."
                                                  })
    context = {'student_list': Student.objects.order_by('sbu_id'), 'major_list': Major.objects.order_by('name')}
    return render(request, 'mast/student_index.html', context)


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
        student.entry_semester = Semester.objects.get(id=int(entry_semester))
        student.requirement_semester = Requirement_Semester.objects.get(id=int(requirement_semester))
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
                                                  'requirement_semesters': Requirement_Semester.objects.order_by(
                                                      'year'),
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