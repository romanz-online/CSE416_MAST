from .models import Student, Major, Season, CoursesTakenByStudent, Comment, StudentCourseSchedule, Semester, Track, \
    TrackCourseSet, CourseInTrackSet, CourseToCourseRelation, Course, CoursePrerequisiteSet, Prerequisite, \
    CourseInstance, CourseStatus

"""
this funciton takes student, prefered class, max_number of classes to take, classes to avoid, time
constraints and graduate semester, and return a dictionary of semester as key and courses as value

time_constaints-> array that index 0 is the start time (no earlier than), index 1 is the end time (no late than)
graduation_semester -> did not use it LOL
max classes-> an int that means the max number of courses to take each semester
avoid classes -> a list of course to avoid 
preferred classes-> nested array, index 0 is the list of favorite courses, and index 1, index2
"""


def classic_suggest(student, prefrered_class, max_classes, avoid_classes, time_constraints, graduation_semester):
    track = Track.objects.filter(id=student.track_id)
    if not track:
        return "does not have track yet"
    # the list of courses to take
    course_list = []
    track = track[0]

    track_set = TrackCourseSet.objects.filter(track=track)
    passed_course_instance = CoursesTakenByStudent.objects.filter(student=student, status=CourseStatus.PASSED)
    Transfer_course_instance = CoursesTakenByStudent.objects.filter(student=student, status=CourseStatus.TRANSFER)
    pending_courses_instance = CoursesTakenByStudent.objects.filter(student=student, status=CourseStatus.PENDING)
    passed_Instances = [i for i in passed_course_instance] + [i for i in Transfer_course_instance] + [i for i in pending_courses_instance]
    passed_courses = []
    for instance in passed_Instances:
        passed_courses.append(instance.course)
    # iterate the tracksets and add unsatisfied course to student course list
    for t_set in track_set:
        temp_courses = []
        set_courses = CourseInTrackSet.objects.filter(course_set=t_set)
        for set_course in set_courses:
            temp_courses.append(set_course.course)
        if not t_set.limiter:
            required_number = t_set.size
            for passed_course in passed_courses:
                if (passed_course in temp_courses):
                    required_number -= 1
            # check the 3 prefred list and put the in the course list if matches
            if (required_number > 0):
                for course1 in prefrered_class[0]:
                    if course1 in temp_courses and course1 not in course_list:
                        course_list.append(course1)
                        required_number -= 1
            if (required_number > 0):
                for course2 in prefrered_class[1]:
                    if course2 in temp_courses and course2 not in course_list:
                        course_list.append(course2)
                        required_number -= 1
                    if required_number <= 0:
                        break
            if (required_number > 0):
                for course3 in prefrered_class[2]:
                    if course3 in temp_courses and course3 not in course_list:
                        course_list.append(course3)
                        required_number -= 1
                    if required_number <= 0:
                        break
            if (required_number > 0):
                for course in temp_courses:
                    if (course not in course_list and course not in avoid_classes):
                        course_list.append(course)
                        required_number -= 1
                    if required_number <= 0:
                        break
        else:
            max_number = t_set.size
            for passed_course in passed_courses:
                if (passed_course in temp_courses):
                    max_number -= 1
            # check the 3 prefred list and put the in the course list if matches
            if (max_number > 0):
                for course1 in prefrered_class[0]:
                    if course1 in temp_courses and course1 not in course_list:
                        course_list.append(course1)
                        max_number -= 1
            if (max_number > 0):
                for course2 in prefrered_class[1] and course2 not in course_list:
                    if course2 in temp_courses:
                        course_list.append(course2)
                        max_number -= 1
                    if max_number <= 0:
                        break
            if (max_number > 0):
                for course3 in prefrered_class[2] and course3 not in course_list:
                    if course3 in temp_courses:
                        course_list.append(course3)
                        max_number -= 1
                    if max_number <= 0:
                        break
    credits_required = track.minimum_credits_required
    current_credits = 0
    # count the credits passed adn in the course plan
    for course in course_list:
        current_credits += course.lower_credit_limit
    for course in passed_courses:
        current_credits += course.lower_credit_limit
    # add new courses to the list if does not have enough credits
    if current_credits < credits_required:
        major_courses = [i for i in Course.objects.filter(department=student.major) if i.number >= 500]
        for course in major_courses:
            if course not in course_list and course not in passed_courses:
                current_credits += course.lower_credit_limit
                course_list.append(course)
                if current_credits >= credits_required:
                    break

    # a dictionary of courses and their prerequisite
    course_and_prerequisite = {}
    # a list of plans

    for course in course_list:
        unsatisfied_prerequisite = get_unsatisfied_prerequisite(student, course.department, course.number)
        course_and_prerequisite[course] = unsatisfied_prerequisite
        for prerequisite in unsatisfied_prerequisite:
            course_and_prerequisite[prerequisite] = get_unsatisfied_prerequisite(student, prerequisite.department,
                                                                                 prerequisite.number)
    schedule_id = generate_plan(student, course_and_prerequisite, max_classes, time_constraints)
    return "Finished generation of classic schedule " + str(schedule_id)


"""
get the unsatisfied prerequisite for the course student want to take
return  a list of courses student need to take in order to fullfill the prerequisite 
"""


def get_unsatisfied_prerequisite(student, department, number):
    # get the course to take and its prerequisite set
    course_want_take = Course.objects.filter(department=department, number=number).first()
    prerequisiteSet = CoursePrerequisiteSet.objects.filter(parent_course=course_want_take)
    # add prerequisite to the list if the student has not take that course or failed
    if (len(prerequisiteSet) == 0):
        return []
    else:
        required_courses = []
        # get courses that must be satisfied
        must_take = Prerequisite.objects.filter(course_set=prerequisiteSet[0])
        if (len(must_take) != 0):
            for prerequisite in must_take:
                prerequisite_course_instance = prerequisite.course
                prerequisite_course = prerequisite_course_instance.course
                if (passCourse(student, prerequisite_course)):
                    continue
                else:
                    required_courses.append(prerequisite_course)
        # get the courses that has or relationship
        optional_set = prerequisiteSet.objects.filter(parent_set=prerequisiteSet[0])
        if (len(optional_set) != 0):
            for set in optional_set:
                satisfy = False
                optional_course_prerequisites = Prerequisite.objects.filter(couse_set=set)
                for course_prerequisite in optional_course_prerequisites:
                    if passCourse(student, course_prerequisite.course.course):
                        satisfy = True
                        break
                # does not satisfy, just take the first course in the set
                if (satisfy == False):
                    course_prerequisite = optional_course_prerequisites[0]
                    required_courses.append(course_prerequisite.course.course)
        return required_courses


"""
return false if the student failed the course or did not take that course
"""


def passCourse(student, course):
    # return true for undergrad course
    if course.number < 500:
        return True
    passed_course_instance = CoursesTakenByStudent.objects.filter(student=student, status=CourseStatus.PASSED)
    Transfer_course_instance = CoursesTakenByStudent.objects.filter(student=student, status=CourseStatus.TRANSFER)
    pending_courses_instance = CoursesTakenByStudent.objects.filter(student=student, status=CourseStatus.PENDING)
    passed_course_instance = passed_course_instance + Transfer_course_instance + pending_courses_instance
    passed = False
    if (len(passed_course_instance) != 0):
        for instance in passed_course_instance:
            if instance.course.course == course:
                passed = True
                break
    return passed


"""
this funciton takes a courseInstance list generate and a courseInstance
if the courseInstance does not have time conflict with course instances in the list 
return False, else return True
"""


def time_conflict(instance_list, instance_to_add, time_constraints):
    if (len(instance_list) == 0):
        return False
    conflict = False
    for instance in instance_list:
        if instance.time_end > instance_to_add.time_start:
            continue
        elif instance.time_start < instance_to_add.time_end:
            continue
        if time_constraints[0] == None or time_constraints[1] == None:
            continue
        elif instance_to_add.time_start > time_constraints[0] or instance_to_add.time_end < time_constraints[1]:
            continue
        else:
            conflict = True
            break
    return conflict


"""
  This function takes student and a dictionary of courses and their prerequisite and generate a course plan
"""


def generate_plan(student, course_and_prerequisite, max_classes, time_constraints):
    schedule_id = 1
    for course in StudentCourseSchedule.objects.filter(student=student):
        if course.schedule_id >= schedule_id:
            schedule_id = course.schedule_id + 1
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    next_semester = get_next_semester(current_semester)
    courses_can_take = []
    for course in course_and_prerequisite.keys():
        if len(course_and_prerequisite[course]) == 0:
            courses_can_take.append(course)
    while (len(course_and_prerequisite) > 0):
        add_new_semester(student, schedule_id, next_semester, courses_can_take, course_and_prerequisite, max_classes,
                         time_constraints)
        courses_can_take = []
        for course in course_and_prerequisite.keys():
            if len(course_and_prerequisite[course]) == 0:
                courses_can_take.append(course)
        next_semester = get_next_semester(next_semester)
    return schedule_id


"""
get the next semester given a semester object
"""


def get_next_semester(current_semester):
    year = current_semester.year
    semester = current_semester.season
    if (current_semester.season == Season.SPRING or current_semester.season == Season.SUMMER):
        semester = Season.FALL
    else:
        semester = Season.SPRING
        year += 1
    return Semester.objects.filter(year=year, season=semester).first()


"""
this function create a new semster with classes that can be taken from the course list
return the number of courses added to that semester
"""


def add_new_semester(student, schedule_id, semester, courses, course_and_prerequisite, max_classes, time_constraints):
    currentInstances = []
    for course in courses:
        # did not exceed max number of courses
        if len(currentInstances) < max_classes:
            # get course instances and check if they can be taken
            courseInstances = CourseInstance.objects.filter(course=course, semester=semester)
            if (len(courseInstances) == 0):
                continue
            else:
                for instance in courseInstances:
                    if time_conflict(currentInstances, instance, time_constraints):
                        continue
                    else:
                        currentInstances.append(instance)
                        course_and_prerequisite.pop(course, None)
                        c = StudentCourseSchedule(student=student, course=instance, schedule_id=schedule_id,
                                                  schedule_type='Classic')
                        c.save()
                        for key in course_and_prerequisite.keys():
                            if course in course_and_prerequisite[key]:
                                course_and_prerequisite[key].remove(course)

        else:
            break
    return len(currentInstances)
