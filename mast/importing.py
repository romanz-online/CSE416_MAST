import re
from bs4 import BeautifulSoup

from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Major, Course, CourseInstance, CoursesTakenByStudent, Semester, Track, \
    TrackCourseSet, CourseInTrackSet, CourseStatus, Grade, Season, CoursePrerequisiteSet, Prerequisite

from . import editing_student


def import_degree_requirements(request):
    # If get request, render page
    if request.method == "GET":
        return render(request, 'mast/import_degree_reqs.html', {'': None})

    # If file uploaded
    degree_file = request.FILES['degree_file']
    # If non-xml file
    if not degree_file.name.endswith('.xml') and not degree_file.name.endswith('.xml\r'):
        messages.error(request, "Incorrect file type.")
        return render(request, 'mast/import_degree_reqs.html', {'': None})

    # Open File using BS4
    infile = open("mast\\test_files\\" + degree_file.name, "r")
    contents = infile.read()
    soup = BeautifulSoup(contents, 'xml')

    # Add Major to database
    department = soup.department.get_text()
    major_name = soup.find("name").get_text()
    semester_season = soup.requirement_semester.season.get_text()
    semester_year = soup.requirement_semester.year.get_text()
    semester = Semester.objects.filter(season=semester_season, year=semester_year)
    if semester:
        semester = semester[0]
        if Major.objects.filter(department=department, name=major_name, requirement_semester=semester):
            old_major = Major.objects.filter(department=department, name=major_name, requirement_semester=semester)[0]
            old_major.delete()
    else:
        semester = Semester(season=semester_season, year=semester_year)
        semester.save()
    m = Major(department=department, name=major_name, requirement_semester=semester)
    m.save()

    # Add tracks + further data to database
    tracks = soup.find_all("Track")
    for track in tracks:

        # Add track to database 
        track_name = track.find("name").get_text()
        # DEFAULT REQ: GPA, MIN CREDITS 
        total_requirements = track.find("total_requirements").get_text()
        thesis = track.find("thesis_required")
        if thesis:
            thesis = True
        else:
            thesis = False
        project = track.find("project_required")
        if project:
            project = True
        else:
            project = False
        min_credits = track.find("minimum_credits_required")
        if min_credits:
            min_credits = min_credits.get_text()
        else:
            min_credits = 30
        t = Track(major=m, name=track_name, thesis_required=thesis, project_required=project,
                  minimum_credits_required=min_credits, total_requirements=total_requirements)
        t.save()

        # Add TrackCourseSets to database 
        track_course_sets = track.find_all("TrackCourseSet")
        for tcs in track_course_sets:

            # Add TCS parents
            if tcs.parent.name == 'Track':
                tcs_size = tcs.find("size")
                if tcs_size:
                    if tcs_size.parent.parent.name == "Track":
                        tcs_size = tcs_size.get_text()
                    else:
                        tcs_size = 1
                else:
                    tcs_size = 1
                tcs_name = tcs.find("name")
                if tcs_name:
                    if tcs_name.parent.parent.name == "Track":
                        tcs_name = tcs_name.get_text() + " - " + track_name
                    else:
                        tcs_name = "Core Set - " + track_name
                else:
                    tcs_name = "Core Set - " + track_name
                tcs_limiter = tcs.find("limiter")
                if tcs_limiter:
                    if tcs_limiter.parent.parent.name == "Track":
                        tcs_limiter = True
                        tcs_upper_credit_limit = tcs.find("upper_credit_limit")
                        if tcs_upper_credit_limit:
                            tcs_size = tcs.find("upper_credit_limit").get_text()
                        else:
                            tcs_size = 3
                    else:
                        tcs_limiter = False
                else:
                    tcs_limiter = False
                tcs_upper_limit = tcs.find("upper_limit")
                if tcs_upper_limit:
                    if tcs_upper_limit.parent.parent.name == "Track":
                        tcs_upper_limit = tcs_upper_limit.get_text()
                    else:
                        tcs_upper_limit = 999
                else:
                    tcs_upper_limit = 999
                tcs_lower_limit = tcs.find("lower_limit")
                if tcs_lower_limit:
                    if tcs_lower_limit.parent.parent.name == "Track":
                        tcs_lower_limit = tcs_lower_limit.get_text()
                    else:
                        tcs_lower_limit = 100
                else:
                    tcs_lower_limit = 100
                tcs_department_limit = tcs.find("department_limit")
                if tcs_department_limit:
                    if tcs_department_limit.parent.parent.name == "Track":
                        tcs_department_limit = tcs_department_limit.get_text()
                    else:
                        tcs_department_limit = 'N/A'
                else:
                    tcs_department_limit = 'N/A'
                tcs_lower_credit_limit = tcs.find("lower_credit_limit")
                if tcs_lower_credit_limit:
                    if tcs_lower_credit_limit.parent.parent.name == "Track":
                        tcs_lower_credit_limit = tcs_lower_credit_limit.get_text()
                    else:
                        tcs_lower_credit_limit = 0
                else:
                    tcs_lower_credit_limit = 0
                tcs_leeway = tcs.find("leeway")
                if tcs_leeway:
                    if tcs_leeway.parent.parent.name == "Track":
                        tcs_leeway = tcs_leeway.get_text()
                    else:
                        tcs_leeway = 0 
                else:
                    tcs_leeway = 0
                tcs_save = TrackCourseSet(track=t, name=tcs_name, size=tcs_size,
                                          limiter=tcs_limiter, upper_limit=tcs_upper_limit, lower_limit=tcs_lower_limit,
                                          lower_credit_limit=tcs_lower_credit_limit,
                                          department_limit=tcs_department_limit, leeway=tcs_leeway)
                tcs_save.save()

                # Add children of TCS 
                for child in tcs.children:
                    if child.parent.parent.name == "Track":
                        if child.name == "TrackCourseSet":
                            tcs_size = child.find("size")
                            if tcs_size:
                                tcs_size = child.find("size").get_text()
                            else:
                                tcs_size = 1
                            tcs_name = child.find("name")
                            if tcs_name:
                                tcs_name = tcs_name.get_text() + " - " + track_name
                            else:
                                tcs_name = "Nested Core Set - " + track_name
                            tcs_limiter = child.find("limiter")
                            if tcs_limiter:
                                tcs_limiter = True
                                tcs_upper_credit_limit = child.find("upper_credit_limit")
                                if tcs_upper_credit_limit:
                                    tcs_size = child.find("upper_credit_limit").get_text()
                                else:
                                    tcs_size = 3
                            else:
                                tcs_limiter = False
                            tcs_upper_limit = child.find("upper_limit")
                            if tcs_upper_limit:
                                tcs_upper_limit = tcs_upper_limit.get_text()
                            else:
                                tcs_upper_limit = 999
                            tcs_lower_limit = child.find("lower_limit")
                            if tcs_lower_limit:
                                tcs_lower_limit = tcs_lower_limit.get_text()
                            else:
                                tcs_lower_limit = 100
                            tcs_department_limit = child.find("department_limit")
                            if tcs_department_limit:
                                tcs_department_limit = tcs_department_limit.get_text()
                            else:
                                tcs_department_limit = 'N/A'
                            tcs_lower_credit_limit = child.find("lower_credit_limit")
                            if tcs_lower_credit_limit:
                                tcs_lower_credit_limit = tcs_lower_credit_limit.get_text()
                            else:
                                tcs_lower_credit_limit = 0
                            tcs_leeway = child.find("leeway")
                            if tcs_leeway:
                                tcs_leeway = tcs_leeway.get_text()
                            else:
                                tcs_leeway = 0 
                            tcs_child_save = TrackCourseSet(track=t, parent_course_set=tcs_save, name=tcs_name,
                                                            size=tcs_size,
                                                            limiter=tcs_limiter, upper_limit=tcs_upper_limit,
                                                            lower_limit=tcs_lower_limit,
                                                            lower_credit_limit=tcs_lower_credit_limit,
                                                            department_limit=tcs_department_limit, 
                                                            leeway = tcs_leeway)
                            tcs_child_save.save()
                            # do one more loop to find courseintracksets and attach them here. 
                            for child_second_loop in child.children:
                                if child_second_loop.name == "CourseInTrackSet":
                                    child_course = child_second_loop.find("course").get_text()
                                    child_course = child_course.split(" ")
                                    # print(child_course)
                                    if Course.objects.filter(department=child_course[0],
                                                             number=child_course[1]).exists():
                                        child_course = Course.objects.get(department=child_course[0],
                                                                          number=child_course[1])
                                    else:
                                        child_course = Course(name=child_course[0], department=child_course[0],
                                                              number=child_course[1])
                                    child_course.save()
                                    course_each_semester = child_second_loop.find("each_semester")
                                    if course_each_semester:
                                        course_each_semester = True
                                    else:
                                        course_each_semester = False
                                    how_many_semesters = child_second_loop.find("how_many_semesters")
                                    if how_many_semesters:
                                        how_many_semesters = how_many_semesters.get_text()
                                    else:
                                        how_many_semesters = 1
                                    course_in_track_set_save = CourseInTrackSet(course_set=tcs_child_save,
                                                                                course=child_course,
                                                                                each_semester=course_each_semester,
                                                                                how_many_semesters=how_many_semesters)
                                    course_in_track_set_save.save()
                        elif child.name == "CourseInTrackSet":
                            child_course = child.find("course").get_text()
                            child_course = child_course.split(" ")
                            # print(child_course)
                            if Course.objects.filter(department=child_course[0], number=child_course[1]).exists():
                                child_course = Course.objects.get(department=child_course[0], number=child_course[1])
                            else:
                                child_course = Course(name=child_course[0], department=child_course[0],
                                                      number=child_course[1])
                            child_course.save()
                            course_each_semester = child.find("each_semester")
                            if course_each_semester:
                                course_each_semester = True
                            else:
                                course_each_semester = False
                            how_many_semesters = child.find("how_many_semesters")
                            if how_many_semesters:
                                how_many_semesters = how_many_semesters.get_text()
                            else:
                                how_many_semesters = 1
                            course_in_track_set_save = CourseInTrackSet(course_set=tcs_save, course=child_course,
                                                                        each_semester=course_each_semester,
                                                                        how_many_semesters=how_many_semesters)
                            course_in_track_set_save.save()

    return render(request, 'mast/import_degree_reqs.html', {'': None})


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
    # print(profiles[0])
    if profiles[
        0] != 'sbu_id,first_name,last_name,email,department,track,entry_semester,entry_year,requirement_version_semester,requirement_version_year,graduation_semester,graduation_year,password' \
            and profiles[
        0] != 'sbu_id,first_name,last_name,email,department,track,entry_semester,entry_year,requirement_version_semester,requirement_version_year,graduation_semester,graduation_year,password\r':
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
            if line[4] and Major.objects.filter(department=line[4]) and line[8] and line[9]:
                requirement_semester = Semester.objects.get(season=line[8], year=line[9])
                if Major.objects.filter(department=line[4], requirement_semester=requirement_semester):
                    student.major = Major.objects.filter(department=line[4], requirement_semester=requirement_semester)[0]
                else:
                    latest_major = Major.objects.filter(department=line[4])[0]
                    for i in Major.objects.filter(department=line[4]):
                        if i.requirement_semester.year > latest_major.requirement_semester.year:
                            latest_major = i
                        if i.requirement_semester.season == Season.WINTER:
                            latest_major = i
                        elif i.requirement_semester.season == Season.FALL and (
                                latest_major.requirement_semester.season == Season.SPRING or latest_major.requirement_semester.season == Season.SUMMER):
                            latest_major = i
                        elif i.requirement_semester.season == Season.SUMMER and latest_major.requirement_semester.season == Season.SPRING:
                            latest_major = i
                    student.major = latest_major
            if line[4] and line[5] \
                    and Major.objects.filter(department=line[4]) and Track.objects.filter(major=student.major, name=line[5]):
                student.track = Track.objects.get(name=line[5], major=student.major)
            if line[6] and line[7]:
                student.entry_semester = Semester.objects.get(season=line[6], year=line[7])
                e = Semester.objects.get(season=line[6], year=line[7])
                if Semester.objects.filter(is_current_semester=True):
                    current_semester = Semester.objects.filter(is_current_semester=True)[0]
                    if e.year < current_semester.year:
                        i = e.year
                        count = 0
                        while i < current_semester.year:
                            if Semester.objects.filter(year=i):
                                count += Semester.objects.filter(year=i).count()
                            i += 1
                        count += 1
                        if current_semester.season == Season.FALL:
                            count += 1
                        student.semesters_enrolled = count
            if line[8] and line[9]:
                student.requirement_semester = Semester.objects.get(season=line[8], year=line[9])
            if line[10] and line[11]:
                student.graduation_semester = Semester.objects.get(season=line[10], year=line[11])
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
    if course_plans[0] != 'sbu_id,department,course_num,section,semester,year,grade' \
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
            student = None
            if line[0] and not Student.objects.get(sbu_id=line[0]):
                messages.error(request, bytes('No student with ID', line[0]))
                continue
            if line[0]:
                new_class.student = Student.objects.get(sbu_id=line[0])
                student = new_class.student
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
            if CoursesTakenByStudent.objects.filter(student=student, course=new_class.course):
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

            student.credits_taken += new_class.credits_taken
            student.save()

            editing_student.sync_course_data(student)

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
    prompt = {'order': 'Order of CSV should be department, course_num, section, semester, year, timeslot'}

    # If get request, render page
    if request.method == "GET":
        return render(request, 'mast/import_courses.html', prompt)

    # If file uploaded
    file_name = request.FILES['file']
    # If non-csv file 
    if not file_name.name.endswith('.csv') and not file_name.name.endswith('.csv\r'):
        messages.error(request, "Incorrect file type.")
        return render(request, 'mast/import_courses.html', prompt)

    file = file_name.read().decode("utf-8")

    lines = file.split('\n')
    if lines[0] != 'department,course_num,section,semester,year,timeslot' \
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
            times = line[5][line[5].index(' ') + 1:]
            start = times[0:times.index('-')]
            end = times[times.index('-') + 1:]
            start = start.replace('\r', '')
            end = end.replace('\r', '')
            # The database wants military time ._.
            if start[-2:] == 'PM':
                t = start[0:2]
                if int(t) != 12:
                    t = int(t) + 12
                    start = str(t) + start[2:]

            # print(end[-2:])
            if end[-2:] == 'PM':
                t = end[0:2]
                if int(t) != 12:
                    t = int(t) + 12
                    end = str(t) + end[2:]
                # print(end)

            course_instance.time_start = start
            course_instance.time_end = end

        course_instance.course = Course.objects.get(department=course.department, number=course.number)
        course_instance.save()
        processed_lines += row
    context = {'course_list': CourseInstance.objects.all()}
    return render(request, 'mast/course_index.html', context)


def scrape_courses(request):
    if request.method == "GET":
        return render(request, 'mast/scrape_courses.html', {'semester_list': Semester.objects.all()})

    course_file = request.FILES['file']
    major = request.POST.get('major')
    semester = request.POST.get('semester')
    major_list = ["CSE", "ESE", "AMS", "BMI"]
    if major not in major_list:
        messages.error(request, "Incorrect major for course offering data.")
        render(request, 'mast/scrape_courses.html', {'semester_list': Semester.objects.all()})

    semester = Semester.objects.get(pk=semester)
    course_data = course_file.read().decode("utf-8", "ignore")
    lines = course_data.split("\r\n")
    text = []
    major_started = False
    for line in lines:
        line = line + "\n"
        regex_test_output = re.compile(major + "  \d\d\d")
        major_regex = re.compile("[A-Z][A-Z][A-Z]\n")
        target_major = re.compile(major + "\n")
        if re.match(target_major, line):
            print(major)
            major_started = True
        elif major_started:
            if re.match(major_regex, line) != None:
                major_started = False
            else:
                if re.match(regex_test_output, line) != None:
                    print(line)
                    text.append(line)
                    text.append("")
                else:
                    if len(text) != 0:
                        text[-1] = text[-1] + line

    # text stores course name and detail , even index is course name, odd index is description
    for course_index in range(len(text) // 2):
        name = text[course_index * 2]
        description = text[course_index * 2 + 1]
        number = int(name[5:8])
        if not Course.objects.filter(department=major, number=number):
            course = Course(department=major, number=number, name=name[9:len(name)], description=description)
            name = name.split(":")[1]
            name.replace("\n", ' ')
            credits = re.search(r'(\d+-)?\d+ credit', description)
            if credits:
                credits = credits.group(0)
                credits = credits.replace(' credit', '')
                if '-' in credits:
                    credit_list = credits.split('-')
                    course.upper_credit_limit = int(credit_list[1])
                    course.lower_credit_limit = int(credit_list[0])
                else:
                    course.upper_credit_limit = int(credits)
            else:
                credits = "3"
                course.upper_credit_limit = int(credits)
            course.save()
        else:
            course = Course.objects.filter(department=major, number=number)[0]
            course.name = name[9:len(name)]
            course.description = description
            credits = re.search(r'(\d+-)?\d+ credit', description)
            if credits:
                credits = credits.group(0)
                credits = credits.replace(' credit', '')
                if '-' in credits:
                    credit_list = credits.split('-')
                    course.upper_credit_limit = int(credit_list[1])
                    course.lower_credit_limit = int(credit_list[0])
                else:
                    course.upper_credit_limit = int(credits)
            else:
                credits = "3"
                course.upper_credit_limit = int(credits)
            course.save()


        CourseInstance.objects.filter(course=course, semester=semester).delete()
        null_semester = CourseInstance.objects.filter(course=course, semester=None)
        courseInstance = None
        if(len(null_semester) ==0):
            courseInstance = CourseInstance(course=course, semester=semester)
            courseInstance.save()
        else:
            courseInstance = null_semester[0]
            courseInstance.semester = semester
            courseInstance.save()
        # prerequisite part
        prerequisite_prefix = re.search(r"Prerequisite.*:", description)
        if prerequisite_prefix:
            prefix_end = prerequisite_prefix.span()[1]
            temp = description[prefix_end: len(description)]  # get the prerequisite part from description
            temp = temp.replace("\n", " ")
            course_re = re.compile(r"[A-Z]{3}.?\d{3}")

            require_set = []  # list of prerequisite class
            relation_set = []  # list of relation; eg relation[i] is the relation of prerequisite[i] and [i-1]
            while re.search(course_re, temp):  # iterate through required courses and check the relation between them
                match = re.search(course_re, temp)
                require_set.append(match.group())
                if re.search(r'or', temp[0:match.span()[0]]):  # relation is or
                    relation_set.append("or")
                else:  # relation is and
                    relation_set.append("and")
                temp = temp[match.span()[1]:len(temp)]
            prerequisite_set = CoursePrerequisiteSet(parent_course=courseInstance)
            prerequisite_set.save()
            j = 0  # counter for the while loop to iterate the course_set

            while j < len(require_set):
                if j == (len(require_set) - 1):  # last course dont nedd check relation, just add it
                    require_major = require_set[j][0:3]
                    require_number = int(require_set[j][-3:])
                    match_course = Course.objects.filter(department=require_major, number=require_number)
                    if len(match_course) == 0:
                        match_course = Course(name="Supplementary", department=require_major, number=require_number)
                        match_course.save()
                        match_courseInstance = CourseInstance(course=match_course)
                        match_courseInstance.save()
                        prereq = Prerequisite(course=match_courseInstance, course_set=prerequisite_set)
                        prereq.save()

                    else:
                        match_courseInstance = CourseInstance.objects.filter(course=match_course[0])
                        if(len(match_courseInstance) !=0):
                            match_courseInstance = match_courseInstance[0]
                        else:
                            match_courseInstance = CourseInstance(course = match_course[0])
                            match_courseInstance.save()
                        prereq = Prerequisite(course=match_courseInstance, course_set=prerequisite_set)
                        prereq.save()
                else:
                    if relation_set[j + 1] == "and":
                        require_major = require_set[j][0:3]
                        require_number = int(require_set[j][-3:])
                        match_course = Course.objects.filter(department=require_major, number=require_number)
                        if len(match_course) == 0:
                            match_course = Course(name="Supplementary", department=require_major, number=require_number)
                            match_course.save()
                            match_courseInstance = CourseInstance(course=match_course)
                            match_courseInstance.save()
                            prereq = Prerequisite(course=match_courseInstance, course_set=prerequisite_set)
                            prereq.save()

                        else:
                            match_courseInstance = CourseInstance.objects.filter(course=match_course[0])
                            if(len(match_courseInstance) !=0):
                                match_courseInstance = match_courseInstance[0]
                            else:
                                match_courseInstance = CourseInstance(course = match_course[0])
                                match_courseInstance.save()
                            prereq = Prerequisite(course=match_courseInstance, course_set=prerequisite_set)
                            prereq.save()
                    # if relation is or
                    elif relation_set[j + 1] == "or":
                        require_major1 = require_set[j][0:3]
                        require_number1 = int(require_set[j][-3:])
                        match_course1 = Course.objects.filter(department=require_major1, number=require_number1)
                        j += 1
                        require_major2 = require_set[j][0:3]
                        require_number2 = int(require_set[j][-3:])
                        match_course2 = Course.objects.filter(department=require_major2, number=require_number2)

                        new_set = CoursePrerequisiteSet(parent_set=prerequisite_set)
                        new_set.save()
                        if len(match_course1) != 0:
                            match_courseInstance = CourseInstance.objects.filter(course=match_course1[0])
                            if(len(match_courseInstance) !=0):
                                match_courseInstance = match_courseInstance[0]
                            else:
                                match_courseInstance = CourseInstance(course = match_course1[0])
                                match_courseInstance.save()
                            prereq = Prerequisite(course=match_courseInstance, course_set=new_set)
                            prereq.save()
                        else:
                            match_course1 = Course(name="Supplementary", department=require_major1,
                                                   number=require_number1)
                            match_course1.save()
                            match_courseInstance = CourseInstance(course=match_course1)
                            match_courseInstance.save()
                            prereq = Prerequisite(course=match_courseInstance, course_set=new_set)
                        if len(match_course2) != 0:
                            match_courseInstance = CourseInstance.objects.filter(course=match_course2[0])
                            if(len(match_courseInstance) !=0):
                                match_courseInstance = match_courseInstance[0]
                            else:
                                match_courseInstance = CourseInstance(course = match_course2[0])
                                match_courseInstance.save()
                            prereq = Prerequisite(course=match_courseInstance, course_set=new_set)
                            prereq.save()
                        else:
                            match_course2 = Course(name="Supplementary", department=require_major2,
                                                   number=require_number2)
                            match_course2.save()
                            match_courseInstance = CourseInstance(course=match_course2)
                            match_courseInstance.save()
                            prereq = Prerequisite(course=match_courseInstance, course_set=new_set)

                j += 1
    return render(request, 'mast/scrape_courses.html', {'semester_list': Semester.objects.all()})
