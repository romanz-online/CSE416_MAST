import re

from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Major, Course, CourseInstance, CoursesTakenByStudent, Semester, Track, CourseStatus, Grade


def import_student(request):
    """
    Imports a student profile through reading a .csv file  
    
        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 

        Returns:
            render (HttpResponse): Returns the respective view containing the respective information of the student schedule retrieved.     
    """

    pro_file = request.FILES['pro_file']

    # User gave a non-csv file 
    if not pro_file.name.endswith('.csv') and not pro_file.name.endswith('.csv\r'):
        messages.error(request, "Incorrect file type for student profiles.")
        return HttpResponseRedirect(reverse('mast:student_index', args=()))

    # Read both files in 
    profile_data = pro_file.read().decode("utf-8")

    # Profiles first, split data and skip header
    profiles = profile_data.split('\n')
    print(profiles[0])
    if profiles[0] != 'sbu_id,first_name,last_name,email,department,track,entry_semester,entry_year,requirement_version_semester,requirement_version_year,graduation_semester,graduation_year,password'\
            and profiles[0] != 'sbu_id,first_name,last_name,email,department,track,entry_semester,entry_year,requirement_version_semester,requirement_version_year,graduation_semester,graduation_year,password\r':
        messages.error(request, "Incorrect labels for profile data.")
        return HttpResponseRedirect(reverse('mast:student_index', args=()))
    profiles.pop(0)

    # Read in new students and add to database
    for row in profiles:
        # Regex for splitting by comma unless in quotes
        line = re.split(',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', row)
        student = Student()
        if line != ['']:
            if Student.objects.filter(sbu_id=line[0]):
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
            if line[4] and line[5] \
                    and Major.objects.filter(department=line[4]) and Track.objects.filter(name=line[5]):
                student.track = Track.objects.get(name=line[5],
                                                  major=Major.objects.filter(department=line[4])[0])
            if line[6] and line[7]:
                student.entry_semester = Semester.objects.get(season=line[6], year=line[7])
            if line[8] and line[9]:
                student.requirement_semester = Semester.objects.get(season=line[8], year=line[9])
            if line[10] and line[11]:
                student.graduation_semester = Semester.objects.get(season=line[10], year=line[11])
                student.graduated = True
            if line[12]:
                student.password = line[12]
            student.save()

    course_file = request.FILES['course_file']
    # Import new students' courses
    return import_grades(request, course_file)


def import_grades_stub(request):
    course_file = request.FILES['course_file']
    return import_grades(request, course_file)


def import_grades(request, course_file):
    """
    Imports a student's grades and coursework through reading a .csv file

        Parameters:
            request (HttpRequest): The request object used to pass states through the system.

        Returns:
            render (HttpResponse): Returns the view of the student index.
    """

    # User gave a non-csv file
    if not course_file.name.endswith('.csv') and not course_file.name.endswith('.csv\r'):
        messages.error(request, "Incorrect file type for course plan data.")
        return HttpResponseRedirect(reverse('mast:student_index', args=()))

    # Read file in
    course_data = course_file.read().decode("utf-8")

    # Import new students' courses
    course_plans = course_data.split('\n')
    if course_plans[0] != 'sbu_id,department,course_num,section,semester,year,grade'\
            and course_plans[0] != 'sbu_id,department,course_num,section,semester,year,grade\r':
        messages.error(request, "Incorrect labels for course plan data.")
        return HttpResponseRedirect(reverse('mast:student_index', args=()))
    course_plans.pop(0)
    for row in course_plans:
        # Regex for splitting by comma unless in quotes
        line = re.split(',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', row)
        if '\r' in line:
            line[line.index('\r')] = ''
        if line != ['']:
            new_class = CoursesTakenByStudent()
            if line[0] and not Student.objects.get(sbu_id=line[0]):
                messages.error(request, bytes('No student with id', line[0]))
                continue
            if line[0]:
                new_class.student = Student.objects.get(sbu_id=line[0])
            if line[1] and Major.objects.filter(department=line[1]) and line[2]:
                department = line[1]
                semester = Semester.objects.filter(season=line[4], year=line[5])[0]
                section = 1 if not line[3] else int(line[3])
                if not Course.objects.filter(department=department, number=int(line[2])):
                    error_string = 'Class ' + line[1] + line[2] + ' could not be found.'
                    messages.error(request, error_string)
                    continue
                course = Course.objects.filter(department=department, number=int(line[2]))[0]
                if CourseInstance.objects.filter(course=course, semester=semester, section=section):
                    new_class.course = CourseInstance.objects.filter(course=course, semester=semester, section=section)[
                        0]
                else:
                    error_string = 'Class ' + line[1] + line[2] + ' section ' + line[3] + ' could not be found.'
                    messages.error(request, error_string)
                    continue
            if CoursesTakenByStudent.objects.filter(student=new_class.student, course=new_class.course):
                error_string = 'Class ' + str(new_class.course) + ' already taken by student ' + str(new_class.student)
                messages.error(request, error_string)
                continue
            if line[6]:
                new_class.grade = get_grade(re.sub(r'\W+', '', line[6]))
                if new_class.grade in [Grade.A, Grade.A_MINUS, Grade.B_PLUS, Grade.B, Grade.B_MINUS, Grade.C_PLUS,
                                       Grade.C, Grade.SATISFIED]:
                    new_class.status = CourseStatus.PASSED
                elif new_class.grade in [Grade.C_MINUS, Grade.D_PLUS, Grade.D, Grade.D_MINUS, Grade.F, Grade.WITHDREW,
                                         Grade.UNSATISFIED]:
                    new_class.status = CourseStatus.FAILED
                else:
                    new_class.status = CourseStatus.PENDING
            else:
                new_class.status = CourseStatus.PENDING
            new_class.save()

    return HttpResponseRedirect(reverse('mast:student_index', args=()))


def get_grade(g):
    """
    Retrieve grade value based on the letter grade.
    """
    d = {'A': Grade.A, 'A-': Grade.A_MINUS, 'B+': Grade.B_PLUS, 'B': Grade.B, 'B-': Grade.B_MINUS, 'C+': Grade.C_PLUS,
         'C': Grade.C, 'C-': Grade.C_MINUS, 'D+': Grade.D_PLUS, 'D': Grade.D, 'D-': Grade.D_MINUS, 'F': Grade.F,
         'W': Grade.WITHDREW, 'S': Grade.SATISFIED, 'U': Grade.UNSATISFIED, 'I': Grade.INCOMPLETE}
    return d[g] if g in d else Grade.NOT_APPLICABLE


def import_courses(request):
    """
    Imports course offerings for the semester.
    
        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 

        Returns:
            render (HttpResponse): Returns the respective view containing the respective information of the student schedule retrieved.     
    """
    prompt = {'order': 'Order of CSV should be department, course_num, section, semester, year, timeslot',
              'courses': Course.objects.all()}

    # If get request, render page
    if request.method == "GET":
        return render(request, 'mast/import_courses.html', prompt)

    # If file uploaded
    file_name = request.FILES['file']
    # If non-csv file 
    if not file_name.name.endswith('.csv') and not file_name.name.endswith('.csv\r'):
        messages.error(request, "Incorrect file type.")

    file = file_name.read().decode("utf-8")

    lines = file.split('\n')
    if lines[0] != 'department,course_num,section,semester,year,timeslot'\
            and lines[0] != 'department,course_num,section,semester,year,timeslot\r':
        messages.error(request, "Incorrect labels for course offering data.")
        return render(request, 'mast/import_courses.html', prompt)

    # Skip header line
    lines.pop(0)

    # Delete all courses from the semesters referenced by the uploaded file
    for row in lines:
        line = re.split(',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', row)
        if line[3] and line[4]:
            semester = Semester.objects.get(season=line[3], year=line[4])
            for course in CourseInstance.objects.all():
                if course.semester == semester:
                    course.delete()

    processed_lines = []
    for row in lines:
        if row in processed_lines:
            continue
        # Regex for splitting by comma unless in quotes
        line = re.split(',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', row)
        course = Course()
        course_instance = CourseInstance()
        if line[0]:
            course.department = line[0]
        if line[1]:
            course.number = line[1]
        if line[0] and line[1]:
            course.name = line[0] + ' ' + line[1]
        if not Course.objects.filter(department=course.department, number=course.number):
            course.save()
        if line[2]:
            course_instance.section = line[2]
        else:
            course_instance.section = 1
        if line[3] and line[4]:
            course_instance.semester = Semester.objects.get(season=line[3], year=line[4])

        # Manipulate string of type DDDD TT:TTMM-TT:TTMM
        if line[5]:
            # Remove days
            course_instance.days = line[5][0:line[5].index(' ')]
            # Get each time
            times = line[5][line[5].index(''):]
            # course_instance.time_start = times[0:times.index('-')]
            # course_instance.time_end = times[times.index('-') + 1:]
        course_instance.course = Course.objects.get(department=course.department, number=course.number)
        course_instance.save()
        processed_lines += row
    context = {'course_list': Course.objects.all()}
    return render(request, 'mast/import_courses.html', context)
