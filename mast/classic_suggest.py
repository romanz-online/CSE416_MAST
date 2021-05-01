from .models import Student, Major, Season, CoursesTakenByStudent, Comment, StudentCourseSchedule, Semester, Track, \
    TrackCourseSet, CourseInTrackSet, CourseToCourseRelation, Course, CoursePrerequisiteSet, Prerequisite, \
    CourseInstance, CourseStatus

from modifying_schedule import sort_semester_list
from smart_suggest import requirements_met
"""
this funciton takes student, prefered class, max_number of classes to take, classes to avoid, time
constraints and graduate semester, and return a dictionary of semester as key and courses as value
"""
def classic_suggest(student, prefrered_class, max_classes, avoid_classes, time_constraints, graduation_semester):
    track = Track.objects.filter(major = student.major, track = student.track)
    if(len(track) ==0):
        return "does not have track yet"
    #the list of courses to take
    course_list = []
    # a dictionary of courses and their prerequisite
    course_and_prerequisite = {}
    # a list of plans
    plans = []

    for course in course_list:
        unsatisfied_prerequisite = get_unsatisfied_prerequisite(student, course.department, course.number)
        course_and_prerequisite[course] = unsatisfied_prerequisite
        for prerequisite in unsatisfied_prerequisite:
            course_and_prerequisite[prerequisite] = get_unsatisfied_prerequisite(student, prerequisite.department, prerequisite.number)

"""
calculate score for the course plan: 
plan-> a dictionary of courses, values are course keys are semeseter and years
prefrered_class -> a nested list of favorite course names
"""
def calculate_score(plan, prefrered_class, avoid_classes):
    score = 0
    for course in plan.values():
        if course in prefrered_class[0]:
            score += 3
        elif course in prefrered_class[1]:
            score += 2
        elif course in prefrered_class[2]:
            score += 1
        elif course in avoid_classes:
            score -= 1
    return score
"""
get the unsatisfied prerequisite for the course student want to take
return  a list of courses student need to take in order to fullfill the prerequisite 
"""
def get_unsatisfied_prerequisite(student, department, number):
    #get the course to take and its prerequisite set
    course_want_take = Course.objects.filter(department = department, number = number).first()
    prerequisiteSet = CoursePrerequisiteSet.objects.filter(course=course_want_take)
    # add prerequisite to the list if the student has not take that course or failed
    if(len(prerequisiteSet) == 0):
        return []
    else:
        required_courses = []
        #get courses that must be satisfied
        must_take = Prerequisite.objects.filter(course_set=prerequisiteSet[0])
        if(len(must_take) !=0):
            for prerequisite in must_take:
                prerequisite_course_instance = prerequisite.course
                prerequisite_course = prerequisite_course_instance.course
                if(passCourse(student, prerequisite_course)):
                    continue
                else:
                    required_courses.append(prerequisite_course)
        # get the courses that has or relationship
        optional_set = prerequisiteSet.objects.filter(parent_set = prerequisiteSet[0])
        if(len(optional_set) !=0):
            for set in optional_set:
                satisfy = False
                optional_course_prerequisites = Prerequisite.filter(couse_set = set)
                for course_prerequisite in optional_course_prerequisites:
                    if passCourse(student, course_prerequisite.course.course):
                        satisfy = True
                        break
                # does not satisfy, just take the first course in the set
                if(satisfy == False):
                     course_prerequisite = optional_course_prerequisites[0]
                     required_courses.append(course_prerequisite.course.course)
        return required_courses

        
"""
return false if the student failed the course or did not take that course
"""

def passCourse(student, course):
    #return true for undergrad course
    if course.number < 500:
        return True
    passed_course_instance = CoursesTakenByStudent.filter(status != CourseStatus.FAILED)
    passed = False
    if(len(passed_course_instance) != 0):
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

def time_conflict(instance_list, instance_to_add):
    if(len(instance_list) ==0):
        return False
    conflict = False
    for instance in instance_list:
        if instance.time_end > instance_to_add.time_start:
            continue
        elif instance.time_start < instance_to_add.time_end:
            continue
        else:
            conflict = True
            break
    return conflict
"""
  This function takes student and a dictionary of courses and their prerequisite and generate a course plan
"""
def generate_plan(student, course_and_prerequisite, max_classes):
    schedule_id = 1
    for course in StudentCourseSchedule.objects.filter(student=student):
        if course.schedule_id >= schedule_id:
            schedule_id = course.schedule_id + 1
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    next_semester = get_next_semester(current_semester)
    courses_can_take = []
    for course in course_and_prerequisite.keys():
        if len(course_and_prerequisite[course]) ==0:
            courses_can_take.append(course)
    while(len(course_and_prerequisite) > 0):
        add_new_semester(schedule_id, next_semester, courses_can_take, course_and_prerequisite, max_classes)
        courses_can_take = []
        for course in course_and_prerequisite.keys():
            if len(course_and_prerequisite[course]) ==0:
                courses_can_take.append(course)
        next_semester = get_next_semester(next_semester)

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
        year +=1
    return Semester.objects.filter(year = year, season = semester)

"""
this function create a new semster with classes that can be taken from the course list
"""

def add_new_semester(schedule_id, semeseter, courses, course_and_prerequisite, max_classes):
    currentInstances = []
    for course in courses:
        # did not exceed max number of courses
        if len(currentInstances) < max_classes:
            courseInstances = CourseInstance.objects.filter(course = course, semester = semester)
            if(len(courseInstances) ==0):
                continue
            else:
                for instance in courseInstances:
                    if time_conflict(currentInstances, instance):
                        continue
                    else:
                        currentInstances.append(instance)
                        course_and_prerequisite.pop(course, None)
                        c = StudentCourseSchedule(student=student, course=instance, schedule_id=schedule_id, schedule_type= 'Classic')
                        c.save()
                        for key in course_and_prerequisite.keys():
                            if course in course_and_prerequisite[key]:
                                course_and_prerequisite[key].remove(course)
                        
        else:
            break
                    