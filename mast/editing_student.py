from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Student, Major, CourseInstance, CoursesTakenByStudent, Grade, CourseStatus, Semester, Track


def edit(request, sbu_id):
    """
    Retrieves and renders a specific student to be edited on the edit screen page
    
        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 
            sbu_id (int): The SBU ID used to retrieve the student object. 

        Returns:
            render (HttpResponse): Returns the respective view containing the respective information of the student retrieved.     
    """
    # Retrieve student using respective SBU ID 
    student = get_object_or_404(Student, pk=sbu_id)
    # Retrieve grade and course status list 
    grade_list = [i[0] for i in Grade.choices]
    course_status_list = [i[0] for i in CourseStatus.choices]
    # Render view with student information

    if not Major.objects.filter(department='N/A'):
        semester = Semester.objects.all()[0]
        none_major = Major(department='N/A',
                           name='(None)',
                           requirement_semester=semester)
        none_major.save()

    track_list = []
    found = False
    for i in Track.objects.all():
        for j in track_list:
            if i.name == j.name and i.major.name == j.major.name:
                found = True
        if not found:
            track_list.append(i)
        found = False

    class RequirementSemesters:
        def __init__(self, track):
            self.track = track
            self.semesters = []

        def add_semester(self, semester):
            self.semesters.append(semester)

    requirement_semesters = []
    for i in track_list:
        new_set = RequirementSemesters(i)
        for j in Track.objects.all():
            if i.name == j.name and i.major.name == j.major.name:
                new_set.add_semester(j.major.requirement_semester)
        requirement_semesters.append(new_set)

    track_list_id = 0
    for i in track_list:
        if student.track and i.name == student.track.name:
            track_list_id = i.id

    class TempCourseInstance:
        def __init__(self, name):
            self.name = name
            self.section = 1
            self.id = 99999

        def __str__(self):
            return 'None'

    transfer_course_list = [i for i in CourseInstance.objects.all()]
    transfer_course_list.insert(0, TempCourseInstance('None'))

    return render(request, 'mast/edit.html', {'student': student,
                                              'course_list': CourseInstance.objects.all(),
                                              'classes_taken': CoursesTakenByStudent.objects.filter(student=student),
                                              'grade_list': grade_list,
                                              'course_status_list': course_status_list,
                                              'semesters': Semester.objects.order_by('year'),
                                              'track_list': track_list,
                                              'transfer_course_list': transfer_course_list,
                                              'requirement_semesters': requirement_semesters,
                                              'track_list_id': track_list_id
                                              })


def delete_record(request, sbu_id):
    """
    Deletes a specific student record from the database.
    
        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 
            sbu_id (int): The SBU ID used to retrieve the student object. 

        Returns:
            render (HttpResponse): Returns the respective view based on the flow of events upon attemping deletion.
    """
    # Retrieve student object 
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        # Attempt to delete student 
        student.delete()
    except:
        # Return an error message if the student could not be deleted.
        grade_list = [i[0] for i in Grade.choices]
        course_status_list = [i[0] for i in CourseStatus.choices]
        return render(request, 'mast/edit.html', {'student': student,
                                                  'major_list': Major.objects.order_by('name'),
                                                  'course_list': CourseInstance.objects.all(),
                                                  'classes_taken': CoursesTakenByStudent.objects.all(),
                                                  'grade_list': grade_list,
                                                  'course_status_list': course_status_list,
                                                  'semesters': Semester.objects.order_by('year'),
                                                  'error_message': "Something went wrong."
                                                  })
    # If the deletion was successful, return to the home page 
    context = {'student_list': Student.objects.order_by('sbu_id'), 'major_list': Major.objects.order_by('name')}
    return render(request, 'mast/student_index.html', context)


def commit_edit(request, sbu_id):
    """
    Commits an edit for a specific student. 
    
        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 
            sbu_id (int): The SBU ID used to retrieve the student object. 

        Returns:
            render (HttpResponse): Returns an error message if the edits could not be committed successfully. 
            HttpResponseRedirect: Redirects back to the student view if the edit was successful.
    """
    # Retrieve student object 
    student = get_object_or_404(Student, pk=sbu_id)
    error_message = 'Something went wrong.'
    try:
        # Attempt to make changes to their data
        first_name = request.GET['first_name']
        last_name = request.GET['last_name']
        email = request.GET['email']

        dummy_track = request.GET['major_track']
        dummy_track = Track.objects.get(id=dummy_track)

        graduated = True if request.GET['graduated'] == 'yes' else False
        withdrew = True if request.GET['withdrew'] == 'yes' else False

        entry_semester = request.GET['entry_semester']
        entry_semester = Semester.objects.get(id=int(entry_semester))

        rsid = str(dummy_track.id) + '_requirement_semester'
        requirement_semester = request.GET[rsid]
        requirement_semester = Semester.objects.get(id=int(requirement_semester))

        dummy_major = dummy_track.major
        major = Major.objects.filter(name=dummy_major.name, requirement_semester=requirement_semester)[0]
        track = Track.objects.filter(name=dummy_track.name, major=major)[0]

        student.first_name = first_name
        student.last_name = last_name
        student.email = email
        student.major = major
        student.track = track
        student.graduated = graduated
        student.withdrew = withdrew
        student.entry_semester = entry_semester
        student.requirement_semester = requirement_semester
        if student.graduated:
            graduation_semester = request.GET['graduation_semester']
            student.graduation_semester = Semester.objects.get(id=int(graduation_semester))

        for course in CoursesTakenByStudent.objects.filter(student=student):
            if course.status != 'Pending':
                new_status = request.GET[str(course.id) + 'status']
                new_grade = request.GET[str(course.id)]
                if course.grade != new_grade:
                    course.grade = new_grade
                if course.status != new_status:
                    course.status = new_status
                    if new_status == 'Pending':
                        course.grade = 'N/A'
                course.save()

        student.gpa = get_gpa(student)

        student.save()
    except:
        # Return an error message if their data could not be saved 
        student = get_object_or_404(Student, pk=sbu_id)
        grade_list = [i[0] for i in Grade.choices]
        course_status_list = [i[0] for i in CourseStatus.choices]

        if not Major.objects.filter(department='N/A'):
            semester = Semester.objects.all()[0]
            none_major = Major(department='N/A',
                               name='(None)',
                               requirement_semester=semester)
            none_major.save()

        track_list = []
        found = False
        for i in Track.objects.all():
            for j in track_list:
                if i.name == j.name and i.major.name == j.major.name:
                    found = True
            if not found:
                track_list.append(i)
            found = False

        class RequirementSemesters:
            def __init__(self, track):
                self.track = track
                self.semesters = []

            def add_semester(self, semester):
                self.semesters.append(semester)

            def __str__(self):
                string_list = [str(i) for i in self.semesters]
                return self.track.name + ' [' + ','.join(string_list) + ']'

        requirement_semesters = []
        for i in track_list:
            new_set = RequirementSemesters(i)
            for j in Track.objects.all():
                if i.name == j.name and i.major.name == j.major.name:
                    new_set.add_semester(j.major.requirement_semester)
            requirement_semesters.append(new_set)

        track_list_id = 0
        for i in track_list:
            if student.track and i.name == student.track.name:
                track_list_id = i.id

        class TempCourseInstance:
            def __init__(self, name):
                self.name = name
                self.section = 1
                self.id = 99999

            def __str__(self):
                return 'None'

        transfer_course_list = [i for i in CourseInstance.objects.all()]
        transfer_course_list.insert(0, TempCourseInstance('None'))

        return render(request, 'mast/edit.html', {'student': student,
                                                  'course_list': CourseInstance.objects.all(),
                                                  'classes_taken': CoursesTakenByStudent.objects.filter(
                                                      student=student),
                                                  'grade_list': grade_list,
                                                  'course_status_list': course_status_list,
                                                  'semesters': Semester.objects.order_by('year'),
                                                  'track_list': track_list,
                                                  'transfer_course_list': transfer_course_list,
                                                  'requirement_semesters': requirement_semesters,
                                                  'track_list_id': track_list_id,
                                                  'error_message': "Something went wrong."
                                                  })
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


def get_gpa(student):
    sum = 0
    total = 0
    for course in CoursesTakenByStudent.objects.all():
        if course.student == student and course.status != 'Pending' and course.status != 'Transfer':
            if course.grade not in ['W', 'S', 'U', 'I', 'N/A']:
                sum += get_grade_number(course.grade)
                total += 1
    if total == 0:
        total = 1
    sum = sum / total
    return format(sum, '.2f')


def get_grade_number(grade):
    """
    Retrieve the grade number of the student based on their letter grade

        Parameters:
            grade (str): The letter grade that the student received.

        Returns:
            dict[grade] (int): The numerical grade converted from the letter grade.
    """
    d = {'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0,
         'D-': 0.7, 'F': 0.0, 'S': 4.0}
    return d[grade]


def add_taken_course(request, sbu_id):
    """
    Adds a taken course to the student database. 

        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 
            sbu_id (int): The SBU ID used to retrieve the student object. 

        Returns:
            HttpResponseRedirect: Redirects back to the student view based on the flow of events.
    """
    # Retrieve student object 
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        # Attempt to add taken course 
        new_course = request.GET['course']
        new_course = CourseInstance.objects.get(id=new_course)
        c = CoursesTakenByStudent(student=student, course=new_course, grade='A')
        c.save()
    except:
        return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))


def add_transfer_course(request, sbu_id):
    # Retrieve student object
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        # Attempt to add transfer course
        course = request.GET['transfer_course']
        grade = request.GET['transfer_course_grade']
        credits = request.GET['transfer_course_credits']
        if course == '99999':
            c = CoursesTakenByStudent(student=student, grade=grade, credits_taken=credits, status=CourseStatus.TRANSFER)
            c.save()
        else:
            c = CoursesTakenByStudent(student=student, course=CourseInstance.objects.get(id=course), grade=grade,
                                      credits_taken=credits, status=CourseStatus.TRANSFER)
            c.save()
    except:
        return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))


def modify_course_in_progress(request, sbu_id, record):
    """
    Modifies a current course in progress to their current state.

        Parameters:
            request (HttpRequest): The request object used to pass states through the system. 
            sbu_id (int): The SBU ID used to retrieve the student object. 
            record (Object): Contains the specific id of the specific record in the list of classes taken.

        Returns:
            HttpResponseRedirect: Redirects back to the student view based on the flow of events.
    """
    # Retrieve student object
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        # Attempt to modify course in progress 
        r = CoursesTakenByStudent.objects.get(id=record)
        if request.GET['action'] == 'pass':
            r.status = CourseStatus.PASSED
            r.grade = 'A'
            r.save()
            student.gpa = get_gpa(student)
            student.save()
        elif request.GET['action'] == 'fail':
            r.status = CourseStatus.FAILED
            r.grade = 'F'
            r.save()
            student.gpa = get_gpa(student)
            student.save()
        elif request.GET['action'] == 'drop':
            r.delete()
            student.save()
        else:
            raise Exception()
    except:
        return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))
