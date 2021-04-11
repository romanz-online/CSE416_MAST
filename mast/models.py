from django.db import models
from datetime import datetime


class Season(models.TextChoices):
    WINTER = 'Winter'
    SPRING = 'Spring'
    SUMMER = 'Summer'
    FALL = 'Fall'
    NOT_APPLICABLE = '(N/A)'


class CourseStatus(models.TextChoices):
    PENDING = 'Pending'
    PASSED = 'Passed'
    FAILED = 'Failed'


class CourseRelation(models.TextChoices):
    XOR = 'XOR'  # means that after you take one class, you can't take the other, ever
    FORBIDDEN_CONCURRENCY = 'Concurrency'  # means that you can't take two specified courses in the same semester
    NONE = 'None'  # default value


class Grade(models.TextChoices):
    A = 'A'
    A_MINUS = 'A-'
    B_PLUS = 'B+'
    B = 'B'
    B_MINUS = 'B-'
    C_PLUS = 'C+'
    C = 'C'
    C_MINUS = 'C-'
    D_PLUS = 'D+'
    D = 'D'
    D_MINUS = 'D-'
    F = 'F'
    WITHDREW = 'W'
    SATISFIED = 'S'
    UNSATISFIED = 'U'
    INCOMPLETE = 'I'
    NOT_APPLICABLE = 'N/A'


class Semester(models.Model):
    season = models.CharField(max_length=6, choices=Season.choices, default=Season.FALL)
    year = models.IntegerField(default=datetime.now().year)
    is_current_semester = models.BooleanField(default=False)

    def __str__(self):
        return self.season + ' ' + str(self.year)


class Course(models.Model):
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=4, default='N/A')
    number = models.IntegerField(default=100)
    lower_credit_limit = models.IntegerField(default=3)
    upper_credit_limit = models.IntegerField(default=3)
    description = models.TextField(max_length=400, default="No class description.")

    def __str__(self):
        return self.department + str(self.number)


class CourseInstance(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, null=True, on_delete=models.SET_NULL)
    time_start = models.TimeField(null=True)
    time_end = models.TimeField(null=True)
    days = models.CharField(max_length=10, null=True)
    section = models.IntegerField(default=1)

    def __str__(self):
        return self.course.department + str(self.course.number) + ':' + str(self.section)


class Major(models.Model):
    department = models.CharField(max_length=4, default='N/A')
    name = models.CharField(max_length=50)
    requirement_semester = models.ForeignKey(Semester, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


# number_of_areas is the number of completed TrackCourseSets required to complete the Track
class Track(models.Model):
    major = models.ForeignKey(Major, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    required_gpa = models.FloatField(default=3.0)
    thesis_required = models.BooleanField(default=False)
    project_required = models.BooleanField(default=False)
    minimum_credits_required = models.IntegerField(default=30)
    total_requirements = models.IntegerField(default=1)

    def __str__(self):
        return str(self.name)


# for core courses (courses that all need to be taken) there will be one TrackCourseSet whose
# size is equal to the number of courses it holds. Its name will be "Core"
#
# if size == 0, then the classes specifically do NOT fulfill this TrackCourseSet's requirements
#
# the limiter variable is used to modify the meaning of the TrackCourseSet's size.
# if limiter is True, then the size denotes how many of the courses a student CAN take,
# whereas if limiter is False, the size denotes how many courses a student HAS TO take
#
# upper_limit and lower_limit are used to denote a range of classes possible to take,
# instead of having 99 entries of CourseInTrackSet
# department_limit simply tells you which department the upper and lower limits are for
#
# the parent_course_set attribute allows this structure to be tree-like
class TrackCourseSet(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    parent_course_set = models.ForeignKey(to='TrackCourseSet', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200, default='Default')
    size = models.IntegerField(default=1)
    limiter = models.BooleanField(default=False)
    upper_limit = models.IntegerField(default=100)
    lower_limit = models.IntegerField(default=999)
    department_limit = models.CharField(max_length=4, default='N/A')

    def __str__(self):
        return self.name


class CourseInTrackSet(models.Model):
    course_set = models.ForeignKey(TrackCourseSet, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    each_semester = models.BooleanField(default=False)
    how_many_semesters = models.IntegerField(default=1)

    def __str__(self):
        return str(self.course)


class CourseToCourseRelation(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    primary_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='primary_course')
    related_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='related_course')
    relation = models.CharField(max_length=20, choices=CourseRelation.choices, default=CourseRelation.NONE)

    def __str__(self):
        if self.relation == CourseRelation.FORBIDDEN_CONCURRENCY:
            return str(self.primary_course) + ' cannot be taken in the same semester as ' + str(
                self.related_course) + '.'
        elif self.relation == CourseRelation.XOR:
            return 'Only one course can be taken between ' + str(self.primary_course) + ' and ' + str(
                self.related_course) + '.'
        else:
            return 'There is no restrictive relation between ' + str(self.primary_course) + ' and ' + str(
                self.related_course) + '.'


class CoursePrerequisiteSet(models.Model):
    parent_course = models.ForeignKey(CourseInstance, on_delete=models.CASCADE, null=True)
    parent_set = models.ForeignKey(to='CoursePrerequisiteSet', on_delete=models.CASCADE, null=True)
    number_required = models.IntegerField(default=1)

    def __str__(self):
        return str(self.parent_course)


class Prerequisite(models.Model):
    course_set = models.ForeignKey(CoursePrerequisiteSet, on_delete=models.CASCADE)
    course = models.ForeignKey(CourseInstance, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.course_set) + ' Prerequisite: ' + str(self.course)


class Director(models.Model):
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=4, default='N/A')
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Student(models.Model):
    sbu_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(default='unknown', max_length=100)
    last_name = models.CharField(default='unknown', max_length=100)
    gpa = models.FloatField(default=4.0)
    email = models.CharField(max_length=100)
    major = models.ForeignKey(Major, null=True, on_delete=models.SET_NULL)
    track = models.ForeignKey(Track, null=True, on_delete=models.SET_NULL)
    graduated = models.BooleanField(default=False)
    withdrew = models.BooleanField(default=False)
    password = models.CharField(max_length=100)
    semesters_enrolled = models.IntegerField(default=1)

    satisfied_courses = models.IntegerField(default=0)
    unsatisfied_courses = models.IntegerField(default=0)
    pending_courses = models.IntegerField(default=0)

    valid_schedule = models.BooleanField(default=True)
    schedule_completed = models.BooleanField(default=False)

    entry_semester = models.ForeignKey(Semester, null=True, on_delete=models.SET_NULL,
                                       related_name='entry_semester')
    requirement_semester = models.ForeignKey(Semester, null=True, on_delete=models.SET_NULL,
                                             related_name='requirement_semester')
    graduation_semester = models.ForeignKey(Semester, null=True, on_delete=models.SET_NULL,
                                            related_name='graduation_semester')

    def __str__(self):
        return str(self.sbu_id)


class CoursesTakenByStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(CourseInstance, null=True, on_delete=models.SET_NULL)
    grade = models.CharField(max_length=3, choices=Grade.choices, default=Grade.NOT_APPLICABLE)
    status = models.CharField(max_length=15, choices=CourseStatus.choices, default=CourseStatus.PENDING)
    credits_taken = models.IntegerField(default=3)

    def __str__(self):
        return str(self.student) + ' - ' + str(self.course)

    def get_status(self):
        return str(self.id) + 'status'


class StudentCourseSchedule(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(CourseInstance, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return str(self.student) + ' - ' + str(self.course) + ' ' + str(self.course.semester)


class Comment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    author = models.CharField(max_length=100, default='no auth')
    text = models.CharField(max_length=1000)
    post_date = models.CharField(max_length=100)
