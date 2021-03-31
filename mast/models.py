from django.db import models
from datetime import datetime


class Department(models.TextChoices):
    AMS = 'AMS'
    BMI = 'BMI'
    CSE = 'CSE'
    ECE = 'ECE'
    NONE = 'N/A'


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
    PREREQUISITE = 'Prerequisite'
    XOR = 'XOR'
    FORBIDDEN_CONCURRENCY = 'Concurrency'
    NONE = 'None'


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
    department = models.CharField(max_length=3, choices=Department.choices, default=Department.NONE)
    number = models.IntegerField(default=100)
    credits = models.IntegerField(default=3)

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
    department = models.CharField(max_length=3, choices=Department.choices, default=Department.NONE)
    name = models.CharField(max_length=50)
    requirement_semester = models.ForeignKey(Semester, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class Track(models.Model):
    major = models.ForeignKey(Major, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    required_gpa = models.FloatField(default=3.0)
    thesis_required = models.BooleanField(default=False)
    project_required = models.BooleanField(default=False)
    minimum_credits_required = models.IntegerField(default=120)
    number_of_areas = models.IntegerField(default=1)

    def __str__(self):
        return str(self.name)


# for core courses (courses that all need to be taken) there will be one RequiredElectiveCourseSet whose
# number_of_required_electives is equal to the number of courses it holds. Its name will be "Core"
class TrackCourseSet(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default='Default')
    number_required = models.IntegerField(default=1)


class CourseInTrackSet(models.Model):
    course_set = models.ForeignKey(TrackCourseSet, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)


# for prerequisite courses, primary_course is the course you're looking at and related_course is its prerequisite
class CourseToCourseRelation(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    primary_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='primary_course')
    related_course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='related_course')
    relation = models.CharField(max_length=20, choices=CourseRelation.choices, default=CourseRelation.NONE)


class Director(models.Model):
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=3, choices=Department.choices, default=Department.NONE)
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
    satisfied_courses = models.IntegerField(default=0)
    unsatisfied_courses = models.IntegerField(default=0)
    pending_courses = models.IntegerField(default=0)
    valid_schedule = models.BooleanField(default=True)
    password = models.CharField(max_length=100)
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
