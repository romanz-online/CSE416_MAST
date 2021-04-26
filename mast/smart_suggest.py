from .models import Student, Major, Season, CoursesTakenByStudent, Comment, StudentCourseSchedule, Semester, Track, \
    TrackCourseSet, CourseInTrackSet, CourseToCourseRelation, Course, CoursePrerequisiteSet, Prerequisite, \
    CourseInstance, CourseStatus

from modifying_schedule import sort_semester_list


#main smart_suggest driver
def smart_suggest(student):
    #get graduated students who have same track and major
    graduate_set = Student.objects.filter(track=student.track, major=student.major, graduated=True)
    #if student has not taken or signed up for any classes, all students are 100% similar
    if student.pending_courses == 0 and student.satisfied_courses == 0:
        similar_schedules = graduate_set
    #else find similar students
    else: 
        similar_schedules = calculate_similarity(student, graduate_set)
    #if no similar_schedules
    if len(similar_schedules) == 0:
        # TODO will need to be updated to a proper render request once UI is in
        return "Not enough data for Smart Suggest"
    #else continue and get course counts
    course_counts = course_counts(student, graduate_set)
    #get next semester number for student
    student_semesters = coures_semester_map_map(sudent)
    current_semester = max(student_semesters.iteritems(), key=operator.itemgetter(1))[0] + 1


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~HELPER FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#calculate similarity between students, and return students with 80% or higher
def calculate_similarity(student, graduate_set):
    student_courses = StudentCourseSchedule.object.filter(student=student)
    student_semesters = map_semester_numbers(student)
    #get dict of classes mapped to semester number
    student_dict = coures_semester_map(student_courses, student_semesters)
    #compare to each graduated student
    for g_s in graduate_set:
        graduated_schedule = StudentCourseSchedule.object.filter(student=g_s)
        graduated_semesters = map_semester_numbers(g_s)
        graduated_dict = coures_semester_map(graduated_schedule, graduated_semesters)
        #keep track of all matching classes
        same_class_in_same_semester = 0
        same_class_in_different_semester = 0
        same_class_in_different_semester = 0 
        #find relation to current student course
        for course in student_dict:
            if course in graduated_dict:
                if graduated_dict.get(course) == student_dict.get(course):
                    same_class_in_same_semester += 1
                else:
                    same_class_in_different_semester += 1
            else:
                class_not_taken += 1

        similarity = (same_class_in_same_semester + (0.5*same_class_in_different_semester) ) / len(student_courses)
        #if similarity is less than 80%, remove graduated student from list
        if similarity < .8:
            graduate_set.remove(g_s)

    return graduate_set


#get dictionary that maps each semester a student has taken courses in to an ordered number
def map_semester_numbers(student):
    semester_map = {}
    #list of all semesters which student has taken classes in 
    semesters = []
    first_year = StudentCourseSchedule.object.filter(student=student)
    for course_instance in student_courses:
        if course_instance.course.semester not in semesters:
            semesters.append(course_instance.course.semester)

    #use function in modyfying schedule to sort semesters
    semesters = sort_semester_list(semesters)
    #dictionary with value as order number
    for i in range(len(semesters)):
        semester_map[semesters[i]] = i


#get dictionary that maps all classes a student has taken to its semester number
def coures_semester_map(student_courses, student_semesters):
    student_dict = {}
    for course in student_courses:
        student_dict[course.course.name] = student_semesters.get(course.course.semester)  
    return student_dict


#get dictionary of course counts from similar students that the current student has not yet taken
def course_counts(student, graduate_set):
    course_counts = {}
    student_courses = StudentCourseSchedule.object.filter(student=student)
    taken_course_list = []
    #get list of names for easy comparison
    for course in student_courses:
        taken_course_list.append(course.course.name)
    
    for g_s in graduate_set:
        graduated_courses = StudentCourseSchedule.object.filter(student=g_s)
        graduated_semesters = map_semester_numbers(g_s)
        graduated_map = coures_semester_map(graduated_courses, graduated_semesters)
        for course in graduated_map:
            #get count for all classes not yet taken by current student
            #if class not taken, and not yet in course_counts
            if course.course.name not in taken_course_list and course.course.name not in course_counts:
                course_counts[course.course.name] = {graduated_semesters.get(course.course.semester):1}
            #else if its not been taken, and already in course_counts
            elif course.course.name not in taken_course_list:
                #semester value already present for course
                if graduated_semesters.get(course.course.semester) in course_counts.keys():
                    course_counts[course][graduated_semesters.get(course.course.semester)] += 1
                #new semester value for course
                else:
                    course_counts[course][graduated_semesters.get(course.course.semester)] = 1


    return course_counts
     

#return boolean indicating if the students's schedule meets all degree reqs
def requirements_met(student):
    if student.unsatisfied_courses == 0:
        return True
    else:
        return False

