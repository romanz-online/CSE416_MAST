import operator

from .modifying_schedule import sort_semester_list
from . import editing_student
from .models import Student, CoursesTakenByStudent, StudentCourseSchedule, TrackCourseSet


# main smart_suggest driver
def smart_suggest_gen(student):
    # get graduated students who have same track and major
    graduate_set = Student.objects.filter(track=student.track, major=student.major, graduated=True)
    # if student has not taken or signed up for any classes, all students are 100% similar
    if student.pending_courses == 0 and student.satisfied_courses == 0:
        similar_schedules = graduate_set
    # else find similar students
    else:
        similar_schedules = calculate_similarity(student, graduate_set)
    # if no similar_schedules
    if len(similar_schedules) == 0:
        # TODO will need to be updated to a proper render request once UI is in
        print("Not enough data for Smart Suggest")
        return
    # else continue and get course counts
    course_counts = course_counter(student, graduate_set)
    # get next semester number for student
    student_courses = StudentCourseSchedule.objects.filter(student=student)
    student_semesters = map_semester_numbers(student, student_courses)
    if student_semesters:
        current_semester = student_semesters[max(student_semesters.items(), key=operator.itemgetter(1))[0]] + 1
    else:
        current_semester = 1
    # get an unused shchedule id
    schedule_id = 1
    for course in StudentCourseSchedule.objects.filter(student=student):
        if course.schedule_id >= schedule_id:
            schedule_id = course.schedule_id + 1
    # while schedule is not complete, add semesters
    while not requirements_met(student, schedule_id):
        if create_semester_schedule(student, current_semester, schedule_id, course_counts) == -1:
            print("Something went wrong")
            return
        else:
            # update course counts to remove added classes
            course_counts = create_semester_schedule(student, current_semester, schedule_id, course_counts)
        # move on to next semester
        current_semester += 1

    print("Finished generation of smart schedule " + str(schedule_id))
    return

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~HELPER FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# calculate similarity between students, and return students with 80% or higher
def calculate_similarity(student, graduate_set):
    student_courses = StudentCourseSchedule.objects.filter(student=student)
    student_semesters = map_semester_numbers(student, student_courses)
    # get dict of classes mapped to semester number
    student_dict = course_semester_map(student_courses, student_semesters)
    # compare to each graduated student
    for g_s in graduate_set:
        graduated_schedule = StudentCourseSchedule.objects.filter(student=g_s)
        graduated_semesters = map_semester_numbers(g_s, graduated_schedule)
        graduated_dict = course_semester_map(graduated_schedule, graduated_semesters)
        # keep track of all matching classes
        same_class_same_semester = 0
        same_class_dif_semester = 0
        class_not_taken = 0
        # find relation to current student course
        for course in student_dict:
            if course in graduated_dict:
                if graduated_dict.get(course) == student_dict.get(course):
                    same_class_same_semester += 1
                else:
                    same_class_dif_semester += 1
            else:
                class_not_taken += 1

        similarity = (same_class_same_semester + (0.5 * same_class_dif_semester)) / len(student_courses)
        # if similarity is less than 80%, remove graduated student from list
        if similarity < .8:
            graduate_set.exclude(sbu_id=g_s.sbu_id)

    return graduate_set


# get dictionary that maps each semester a student has taken courses in to an ordered number
def map_semester_numbers(student, student_courses):
    semester_map = {}
    # list of all semesters which student has taken classes in
    semesters = []
    first_year = StudentCourseSchedule.objects.filter(student=student)
    for course_instance in student_courses:
        if course_instance.course.semester not in semesters:
            semesters.append(course_instance.course.semester)

    # use function in modyfying schedule to sort semesters
    semesters = sort_semester_list(semesters)
    # dictionary with value as order number
    for i in range(len(semesters)):
        semester_map[semesters[i]] = i
    return semester_map

# get dictionary that maps all classes a student has taken to its semester number
def course_semester_map(student_courses, student_semesters):
    student_dict = {}
    for course in student_courses:
        student_dict[course.course.course.name] = student_semesters.get(course.course.semester)
    return student_dict


# get dictionary of course counts from similar students that the current student has not yet taken
def course_counter(student, graduate_set):
    course_counts = {}
    student_courses = StudentCourseSchedule.objects.filter(student=student)
    taken_course_list = []
    # get list of names for easy comparison
    for course in student_courses:
        taken_course_list.append(course.course.course.name)

    for g_s in graduate_set:
        graduated_courses = StudentCourseSchedule.objects.filter(student=g_s)
        graduated_semesters = map_semester_numbers(g_s, graduated_courses)
        graduated_map = course_semester_map(graduated_courses, graduated_semesters)
        for course in graduated_map:
            # get count for all classes not yet taken by current student
            # if class not taken, and not yet in course_counts
            if course.course.course.name not in taken_course_list and course.course.course.name not in course_counts:
                course_counts[course.course.course.name] = {graduated_semesters.get(course.course.semester): 1}
            # else if its not been taken, and already in course_counts
            elif course.course.course.name not in taken_course_list:
                # semester value already present for course
                if graduated_semesters.get(course.course.semester) in course_counts.keys():
                    course_counts[course][graduated_semesters.get(course.course.semester)] += 1
                # new semester value for course
                else:
                    course_counts[course][graduated_semesters.get(course.course.semester)] = 1

    return course_counts


# return boolean indicating if the students's schedule meets all degree reqs
def requirements_met(student, schedule_id):
    if not student.track:
        return False
    taken_courses = [i for i in CoursesTakenByStudent.objects.filter(student=student)]
    scheduled_courses = [i for i in StudentCourseSchedule.objects.filter(student=student, schedule_id=schedule_id)]
    courses_to_check = taken_courses + scheduled_courses
    track = student.track

    unsatisfied_requirements = track.total_requirements - 2

    # find satisfied and pending requirements
    parent_course_sets = TrackCourseSet.objects.filter(track=track, parent_course_set=None)
    for i in parent_course_sets:
        # this is inefficient but i didn't want to duplicate the method just to change 2 lines
        if editing_student.find_requirements(courses_to_check, i, False):
            unsatisfied_requirements -= 1
        if editing_student.find_requirements(courses_to_check, i, True):
            unsatisfied_requirements -= 1

    # yes, this is correct
    # makes no sense, but whatever
    return unsatisfied_requirements


# add courses to a semester in student schedule
def create_semester_schedule(student, semester, schedule_id, course_counts):
    # get classes taken most often in
    this_semesters_classes = []
    for course in course_counts:
        if max(course_counts[course], key=course_counts[course].get) == semester:
            this_semesters_classes.append(course)

    # error, no classes found
    if len(this_semesters_classes) == 0:
        return -1

    # for each class in that are most often taken in this semester, add all that student met prereqs for
    for course in this_semesters_classes:
        if prereqs_met(student, course, schedule_id):
            c = StudentCourseSchedule(student=student, course=course, schedule_id=schedule_id, schedule_type='Smart')
            c.save()
            course_counts.pop(course)
        # can't take it this semester, save it for next most popular semester
        else:
            course_counts[course].pop(semester)

    # return course counts with the taken classes removed
    return course_counts

def prereqs_met(student, course, schedule_id):
    student_courses = StudentCourseSchedule.objects.filter(student=student,
                                                           schedule_id=schedule_id) | StudentCourseSchedule.objects.filter(
        student=student, schedule_id=0)
    prereq_set = CoursePrerequisiteSet.objects.filter(parent_course=course)
    for prereq in Prerequisite.objects.filter(course_set=prereq_set):
        if prereq not in student_courses:
            return False

    for nested_set in CoursePrerequisiteSet.objects.filter(parent_set=prereq_set):
        met = False
        for prereq in Prerequisite.objects.filter(course_set=nested_set):
            if prereq in student_courses:
                met = True
        if not met:
            return False

    return True
