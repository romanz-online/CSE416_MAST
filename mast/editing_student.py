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

    class MajorTrack:
        def __init__(self, major, track, id):
            self.major = major
            self.track = track
            self.id = id

    if not Major.objects.filter(department='N/A'):
        semester = Semester.objects.all()[0]
        none_major = Major(department='N/A',
                           name='(None)',
                           requirement_semester=semester)
        none_major.save()
    major_track_list = []
    for m in Major.objects.all():
        for t in Track.objects.all():
            if t.major == m:
                major_track_list.append(MajorTrack(m.name, t.name, t.id))

    for i in major_track_list:
        if i.id == student.track.id:
            print(i.track, ' - ', student.track)

    return render(request, 'mast/edit.html', {'student': student,
                                              'course_list': CourseInstance.objects.all(),
                                              'classes_taken': CoursesTakenByStudent.objects.all(),
                                              'grade_list': grade_list,
                                              'course_status_list': course_status_list,
                                              'semesters': Semester.objects.order_by('year'),
                                              'major_track_list': major_track_list
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
    try:
        # Attempt to make changes to their data
        first_name = request.GET['first_name']
        last_name = request.GET['last_name']
        email = request.GET['email']
        track = request.GET['major_track']
        track = Track.objects.get(id=track)
        major = track.major
        graduated = True if request.GET['graduated'] == 'yes' else False
        withdrew = True if request.GET['withdrew'] == 'yes' else False
        entry_semester = request.GET['entry_semester']
        requirement_semester = request.GET['requirement_semester']

        student.first_name = first_name
        student.last_name = last_name
        student.email = email
        student.major = major
        student.track = track
        student.graduated = graduated
        student.withdrew = withdrew
        student.entry_semester = Semester.objects.get(id=int(entry_semester))
        student.requirement_semester = Semester.objects.get(id=int(requirement_semester))
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

        sum = 0
        total = 0
        for course in CoursesTakenByStudent.objects.all():
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
        # Return an error message if their data could not be saved 
        student = get_object_or_404(Student, pk=sbu_id)
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
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


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