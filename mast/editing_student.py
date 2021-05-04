from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Student, Major, CourseInstance, CoursesTakenByStudent, Grade, CourseStatus, Semester, Track, \
    TrackCourseSet, CourseInTrackSet, StudentCourseSchedule

from . import searching


@login_required
def student_edit(request, sbu_id):
    if request.user.groups.filter(name='Director'):
        return edit(request, sbu_id)

    student = get_object_or_404(Student, pk=sbu_id)

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

    return render(request, 'mast/edit.html', {'student': student,
                                              'is_student': True,
                                              'classes_taken': CoursesTakenByStudent.objects.filter(student=student),
                                              'semesters': Semester.objects.order_by('year'),
                                              'track_list': track_list,
                                              'requirement_semesters': requirement_semesters,
                                              'track_list_id': track_list_id
                                              })


@login_required
def edit(request, sbu_id):
    if request.user.groups.filter(name='Student'):
        return student_edit(request, sbu_id)

    is_student = False
    if request.user.groups.filter(name='Student'):
        is_student = True

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
                                              'is_student': is_student,
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


@login_required
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
        return edit(request, sbu_id)
    return searching.student_index(request)


@login_required
def student_commit_edit(request, sbu_id):

    student = get_object_or_404(Student, pk=sbu_id)
    try:
        changed = False

        first_name = request.GET['first_name']
        last_name = request.GET['last_name']
        email = request.GET['email']

        dummy_track = request.GET['major_track']
        dummy_track = Track.objects.get(id=dummy_track)

        rsid = str(dummy_track.id) + '_requirement_semester'
        requirement_semester = request.GET[rsid]
        if requirement_semester:
            requirement_semester = Semester.objects.get(id=int(requirement_semester))
        else:
            requirement_semester = None

        dummy_major = dummy_track.major
        if requirement_semester:
            major = Major.objects.filter(name=dummy_major.name, requirement_semester=requirement_semester)[0]
        else:
            major = Major.objects.filter(name=dummy_major.name)[0]
        track = Track.objects.filter(name=dummy_track.name, major=major)[0]

        if student.first_name != first_name:
            student.first_name = first_name
            changed = True
        if student.last_name != last_name:
            student.last_name = last_name
            changed = True
        if student.email != email:
            student.email = email
            changed = True
        if student.major != major:
            student.major = major
            changed = True
        if student.track != track:
            student.track = track
            changed = True
        if student.requirement_semester != requirement_semester and requirement_semester:
            student.requirement_semester = requirement_semester
            changed = True
        if student.graduated:
            graduation_semester = request.GET['graduation_semester']
            graduation_semester = Semester.objects.get(id=int(graduation_semester))
            if student.graduation_semester != graduation_semester:
                student.graduation_semester = graduation_semester
                changed = True

        for course in CoursesTakenByStudent.objects.filter(student=student):
            if course.status != 'Pending':
                new_status = request.GET[str(course.id) + 'status']
                new_grade = request.GET[str(course.id)]
                if course.grade != new_grade:
                    course.grade = new_grade
                    changed = True
                if course.status != new_status:
                    course.status = new_status
                    changed = True
                    if new_status == 'Pending':
                        course.grade = 'N/A'
                course.save()

        gpa = get_gpa(student)
        if student.gpa != gpa:
            student.gpa = gpa
            changed = True

        student.save()

        if changed:
            sync_course_data(student)
    except:
        return student_edit(request, sbu_id)
    return HttpResponseRedirect(reverse('mast:detail', args=(sbu_id,)))


@login_required
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
        changed = False
        # Attempt to make changes to their data
        first_name = request.GET['first_name']
        last_name = request.GET['last_name']
        email = request.GET['email']

        graduated = True if request.GET['graduated'] == 'yes' else False
        withdrew = True if request.GET['withdrew'] == 'yes' else False

        entry_semester = request.GET['entry_semester']
        entry_semester = Semester.objects.get(id=int(entry_semester))

        dummy_track = request.GET['major_track']
        dummy_track = Track.objects.get(id=dummy_track)

        rsid = str(dummy_track.id) + '_requirement_semester'
        requirement_semester = request.GET[rsid]
        if requirement_semester:
            requirement_semester = Semester.objects.get(id=int(requirement_semester))
        else:
            requirement_semester = None

        dummy_major = dummy_track.major
        if requirement_semester:
            major = Major.objects.filter(name=dummy_major.name, requirement_semester=requirement_semester)[0]
        else:
            major = Major.objects.filter(name=dummy_major.name)[0]
        track = Track.objects.filter(name=dummy_track.name, major=major)[0]

        if student.first_name != first_name:
            student.first_name = first_name
            changed = True
        if student.last_name != last_name:
            student.last_name = last_name
            changed = True
        if student.email != email:
            student.email = email
            changed = True
        if student.major != major:
            student.major = major
            changed = True
        if student.track != track:
            student.track = track
            changed = True
        if student.graduated != graduated:
            student.graduated = graduated
            changed = True
        if student.withdrew != withdrew:
            student.withdrew = withdrew
            changed = True
        if student.entry_semester != entry_semester:
            student.entry_semester = entry_semester
            changed = True
        if student.requirement_semester != requirement_semester and requirement_semester:
            student.requirement_semester = requirement_semester
            changed = True
        if student.graduated:
            graduation_semester = request.GET['graduation_semester']
            graduation_semester = Semester.objects.get(id=int(graduation_semester))
            if student.graduation_semester != graduation_semester:
                student.graduation_semester = graduation_semester
                changed = True

        for course in CoursesTakenByStudent.objects.filter(student=student):
            if course.status != CourseStatus.PENDING:
                new_status = request.GET[str(course.id) + 'status']
                new_grade = request.GET[str(course.id)]
                if course.grade != new_grade:
                    course.grade = new_grade
                    changed = True
                if course.status != new_status:
                    course.status = new_status
                    changed = True
                    if new_status == CourseStatus.PENDING:
                        course.grade = 'N/A'
                    if new_status == CourseStatus.FAILED:
                        student.credits_taken -= course.credits_taken
                course.save()

        gpa = get_gpa(student)
        if student.gpa != gpa:
            student.gpa = gpa
            changed = True

        student.save()

        if changed:
            sync_course_data(student)
    except:
        return edit(request, sbu_id)
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


@login_required
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


@login_required
def add_transfer_course(request, sbu_id):
    # Retrieve student object
    student = get_object_or_404(Student, pk=sbu_id)
    try:
        # Attempt to add transfer course
        course = request.GET['transfer_course']
        grade = request.GET['transfer_course_grade']
        credits_taken = request.GET['transfer_course_credits']
        if course == '99999':
            c = CoursesTakenByStudent(student=student, grade=grade, credits_taken=credits_taken,
                                      status=CourseStatus.TRANSFER)
            c.save()
        else:
            c = CoursesTakenByStudent(student=student, course=CourseInstance.objects.get(id=course), grade=grade,
                                      credits_taken=credits_taken, status=CourseStatus.TRANSFER)
            c.save()

        transfer_credits = 0
        for i in CoursesTakenByStudent.objects.filter(student=student):
            if i.status == CourseStatus.TRANSFER:
                transfer_credits += i.credits_taken
        if 12 - transfer_credits < credits_taken:
            credits_taken = (credits_taken + transfer_credits) - 12
        student.credits_taken += credits_taken
        student.save()
        sync_course_data(student)
    except:
        return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))


@login_required
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
            r.grade = Grade.A
            r.save()
            student.gpa = get_gpa(student)
            student.credits_taken += r.credits_taken
            student.save()
            sync_course_data(student)
        elif request.GET['action'] == 'fail':
            r.status = CourseStatus.FAILED
            r.grade = Grade.F
            r.save()
            student.gpa = get_gpa(student)
            student.save()
            sync_course_data(student)
        elif request.GET['action'] == 'drop':
            r.delete()
            student.save()
        else:
            raise Exception()
    except:
        return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))
    return HttpResponseRedirect(reverse('mast:edit', args=(sbu_id,)))


def find_requirements(taken_courses, course_set, for_pending):
    number_taken = 0
    if course_set.size:
        if not course_set.limiter:
            if course_set.lower_limit != 100 and course_set.upper_limit != 999:
                taken_course_lookup = len([i for i in taken_courses if
                                           course_set.lower_limit <= i.course.course.number <= course_set.upper_limit])
                if taken_course_lookup:
                    number_taken += taken_course_lookup
                    if course_set.leeway:
                        number_taken -= course_set.leeway // 3
            for course in CourseInTrackSet.objects.filter(course_set=course_set):
                if for_pending:
                    taken_course_lookup = len([i for i in taken_courses if
                                               i.course.course == course.course and i.course.status == CourseStatus.PENDING])
                else:
                    print(len(taken_course_lookup))
                    taken_course_lookup = len([i for i in taken_courses if
                                               i.course.course == course.course and i.status == CourseStatus.PASSED])
                number_taken += taken_course_lookup
            for track in TrackCourseSet.objects.filter(parent_course_set=course_set):
                if track.lower_limit != 100 and track.upper_limit != 999:
                    taken_course_lookup = len(
                        [i for i in taken_courses if track.lower_limit <= i.course.course.number <= track.upper_limit])
                    number_taken += taken_course_lookup
                else:
                    for course in CourseInTrackSet.objects.filter(course_set=track):
                        if for_pending:
                            taken_course_lookup = len([i for i in taken_courses if
                                                       i.course.course == course.course and i.course.status == CourseStatus.PENDING])
                        else:
                            taken_course_lookup = len([i for i in taken_courses if
                                                       i.course.course == course.course and i.status == CourseStatus.PASSED])
                        if taken_course_lookup >= track.size:
                            number_taken += track.size
                        else:
                            number_taken += taken_course_lookup
            for i in TrackCourseSet.objects.filter(parent_course_set=course_set):
                if find_requirements(taken_courses, i, for_pending):
                    number_taken += 1
            if "Elective" not in course_set.name and number_taken >= course_set.size:
                return True
    return number_taken


def adjust_credits_recurse(course_set, credits_taken, taken_course_instances, taken_courses):
    if course_set.limiter:
        credits_accumulated_in_set = 0

        # adding up credits from normal courses
        for course in CourseInTrackSet.objects.filter(course_set=course_set):
            if course.course in taken_courses:
                course_instance = None
                for instance in taken_course_instances:
                    if instance.course == course.course:
                        course_instance = instance
                credits_accumulated_in_set += course_instance.credits_taken

        # adding up credits from ranges
        if course_set.department_limit:
            for course in taken_courses:
                if course.department == course_set.department_limit and course_set.lower_limit <= course.number <= course_set.upper_limit:
                    course_instance = None
                    for instance in taken_course_instances:
                        if instance.course == course:
                            course_instance = instance
                    credits_accumulated_in_set += course_instance.credits_taken

        # subtracting credits
        if credits_accumulated_in_set > course_set.size:
            credits_taken -= (credits_accumulated_in_set - course_set.size)

    # recursive call for nested sets
    for nested_set in TrackCourseSet.objects.filter(parent_course_set=course_set):
        credits_taken = adjust_credits_recurse(nested_set, credits_taken, taken_course_instances, taken_courses)

    return credits_taken


def adjust_credits(student, taken_courses):
    # setting up variables
    track = student.track
    credits_taken = student.credits_taken
    taken_course_instances = [i for i in taken_courses if
                              i.status == CourseStatus.PASSED or i.status == CourseStatus.TRANSFER]
    taken_courses = [i.course.course for i in taken_course_instances]

    # call to recursive function
    for course_set in TrackCourseSet.objects.filter(track=track, parent_course_set=None):
        credits_taken = adjust_credits_recurse(course_set, credits_taken, taken_course_instances, taken_courses)

    student.credits_taken = credits_taken
    student.save()


def sync_course_data(student):
    if not student.track:
        return
    taken_courses = CoursesTakenByStudent.objects.filter(student=student)
    scheduled_courses = StudentCourseSchedule.objects.filter(student=student, schedule_id=0)
    track = student.track

    satisfied_requirements = 0
    pending_requirements = 2
    unsatisfied_requirements = student.track.total_requirements - 2

    adjust_credits(student, taken_courses)

    if student.credits_taken >= track.minimum_credits_required:
        satisfied_requirements += 1
        pending_requirements -= 1

    # if student.graduated:
    #     satisfied_requirements = student.track.total_requirements
    #     pending_requirements = 0
    #     unsatisfied_requirements = 0
    # else:
        # find satisfied and pending requirements
    parent_course_sets = TrackCourseSet.objects.filter(track=track, parent_course_set=None)
    for i in parent_course_sets:
        if find_requirements(taken_courses, i, False):
            satisfied_requirements += 1
            unsatisfied_requirements -= 1
        if find_requirements(scheduled_courses, i, True):
            print('found pending')
            pending_requirements += 1
            unsatisfied_requirements -= 1

    student.satisfied_courses = satisfied_requirements
    student.pending_courses = pending_requirements
    student.unsatisfied_courses = unsatisfied_requirements
    student.save()
