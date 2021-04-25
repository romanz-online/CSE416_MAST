from .models import Student, Major, Season, CoursesTakenByStudent, Comment, StudentCourseSchedule, Semester, Track, \
    TrackCourseSet, CourseInTrackSet, CourseToCourseRelation, Course, CoursePrerequisiteSet, Prerequisite, \
    CourseInstance, CourseStatus

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



#calculate similarity between students, and return students with 80% or higher
def calculate_similarity(student, graduate_set):
    student_courses = StudentCourseSchedule.object.filter(student=student)
    student_semesters = map_semester_numbers(student)
    for g_s in graduate_set:
        graduated_schedule = StudentCourseSchedule.object.filter(student=g_s)
        same_class_in_same_semester = 0
        same_class_in_different_semester = 0
        class_not_taken = 0 
        #for course in student_courses:


#get dictionary that maps each semester a student has taken courses in to an ordered number
def map_semester_numbers(student):
    #dictionary mapping each season to its order number
    seasons = {'Winter':1, 'Spring':2, 'Summer':3, 'Fall':4}
    semester_map = {}
    first_year = StudentCourseSchedule.object.filter(student=student).aggregate(Min(''))
    for course in student_courses:


