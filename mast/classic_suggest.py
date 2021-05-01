from .models import Student, Major, Season, CoursesTakenByStudent, Comment, StudentCourseSchedule, Semester, Track, \
    TrackCourseSet, CourseInTrackSet, CourseToCourseRelation, Course, CoursePrerequisiteSet, Prerequisite, \
    CourseInstance, CourseStatus

from modifying_schedule import sort_semester_list
from smart_suggest import requirements_met

def classic_suggest(student, prefrered_class, max_credits, avoid_classes, time_constraints):
    track = Track.objects.filter(major = student.major, track = student.track)
    if(len(track) ==0):
        return "does not have track yet"

    courseToTake = {}
    
    

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
    passed_course_instance = CoursesTakenByStudent.filter(status != CourseStatus.FAILED)
    passed = False
    if(len(passed_course_instance) != 0):
        for instance in passed_course_instance:
            if instance.course.course == course:
                passed = True
                break
    return passed
