import re

from django.shortcuts import render
from django.contrib import messages
from .models import Student, Major, Course, Classes_Taken_by_Student, Semester, Requirement_Semester, Tracks_in_Major


def import_student(request):
    context = {'': None}

    # if we just taking a look
    if request.method == "GET":
        return render(request, 'mast/import_student.html', context)

    pro_file = request.FILES['pro_file']
    course_file = request.FILES['course_file']

    # if the user is dumb and gave us a non-csv
    if not pro_file.name.endswith('.csv'):
        messages.error(request, "Incorrect file type for student profiles.")
    if not course_file.name.endswith('.csv'):
        messages.error(request, "Incorrect file type for course plan data.")

    # read both files in
    profile_data = pro_file.read().decode("utf-8")
    course_data = course_file.read().decode("utf-8")

    # profiles first, split data and skip header
    profiles = profile_data.split('\n')
    profiles.pop(0)

    # read in new students and add to database
    for row in profiles:
        # regex for splitting by comma unless in quotes
        line = re.split(',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', row)
        student = Student()
        if Student.objects.get(sbu_id=line[0]):
            s = Student.objects.get(sbu_id=line[0])
            s.delete()
        if line[0]:
            student.sbu_id = line[0]
        if line[1]:
            student.first_name = line[1]
        if line[2]:
            student.last_name = line[2]
        if line[3]:
            student.email = line[3]
        if line[4] and Major.objects.filter(department=line[4]):
            student.major = Major.objects.filter(department=line[4])[0]
        if line[4] and line[5] and Major.objects.filter(department=line[4]) and Tracks_in_Major.objects.filter(
                name=line[5]):
            student.track = Tracks_in_Major.objects.get(name=line[5], major=Major.objects.filter(department=line[4])[0])
        if line[6] and line[7]:
            student.entry_semester = Semester.objects.get(season=line[6], year=line[7])
        if line[8] and line[9]:
            student.requirement_semester = Requirement_Semester.objects.get(season=line[8], year=line[9])
        if line[10]:
            student.graduation_season = line[10]
        if line[11]:
            student.graduation_year = line[11]
        if line[10] and line[11]:
            student.graduated = True
        if line[12]:
            student.password = line[12]
        student.save()

    # import new students' courses
    course_plans = course_data.split('\n')
    course_plans.pop(0)

    for row in course_plans:
        # regex for splitting by comma unless in quotes
        line = re.split(',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', row)
        new_class = Classes_Taken_by_Student()
        if line[0] and not Student.objects.get(sbu_id=line[0]):
            messages.error(request, bytes('No student with id', line[0]))
            continue
        if line[0]:
            new_class.student = Student.objects.get(sbu_id=line[0])
        if line[1] and Major.objects.filter(department=line[1]):
            new_class.major = Major.objects.filter(department=line[1])[0]

    return render(request, 'mast/import_student.html', context)


def import_courses(request):
    # all courses
    courses = Course.objects.all()
    prompt = {'order': 'Order of CSV should be department, course_num, section, semester, year, timesot',
              'courses': courses}

    # if get request, render page
    if request.method == "GET":
        return render(request, 'mast/import_courses.html', prompt)

    # if file uploaded
    file_name = request.FILES['file']
    # if the user is dumb and gave us a non-csv
    if not file_name.name.endswith('.csv'):
        messages.error(request, "Incorrect file type.")

    file = file_name.read().decode("utf-8")
    lines = file.split('\n')
    # skip header line
    lines.pop(0)
    for row in lines:
        # regex for splitting by comma unless in quotes
        line = re.split(',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', row)
        course = Course()
        if line[0]:
            course.department = line[0]
        if line[1]:
            course.number = line[1]
        if line[0] and line[1]:
            course.name = line[0] + ' ' + line[1]
        if line[2]:
            course.section = line[2]
        else:
            course.section = 1
        if line[3] and line[4]:
            course.semester = Semester.objects.get(season=line[3], year=line[4])
        # manipulate string of type DDDD TT:TTMM-TT:TTMM
        if line[5]:
            # remove days
            course.days = line[5][0:line[5].index(' ')]
            # get each time
            times = line[5][line[5].index(''):]
            time_start = times[0:times.index('-')]
            time_end = times[times.index('-') + 1:]
        course.save()
    context = {'course_list': Course.objects.all()}
    return render(request, 'mast/import_courses.html', context)
