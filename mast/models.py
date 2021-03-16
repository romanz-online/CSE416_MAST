from django.db import models
from datetime import datetime


class Season(models.TextChoices):
    WINTER = 'Winter'
    SPRING = 'Spring'
    SUMMER = 'Summer'
    FALL = 'Fall'


class CourseStatus(models.TextChoices):
    SATISFIED = 'Satisfied'
    PENDING = 'Pending'
    UNSATISFIED = 'Unsatisfied'


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


class Course(models.Model):
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=10)
    number = models.IntegerField()
    semester_season = models.CharField(max_length=6, choices=Season.choices, default=Season.FALL)
    semester_year = models.IntegerField()
    timeslot = models.TimeField()
    section = models.IntegerField()

    def __str__(self):
        return self.department + str(self.number) + ':' + str(self.section)


class Prerequisite_Classes_for_Course(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    prerequisite_name = models.CharField(max_length=100)
    prerequisite_department = models.CharField(max_length=10)
    prerequisite_number = models.IntegerField()


class Major(models.Model):
    name = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    requirement_semester_season = models.CharField(max_length=6, choices=Season.choices, default=Season.FALL)
    requirement_semester_year = models.IntegerField(default=datetime.now().year)

    def __str__(self):
        return self.name


class Required_Classes_for_Track(models.Model):
    major = models.ForeignKey(Major, on_delete=models.CASCADE)
    track = models.CharField(max_length=50)
    required_class = models.ForeignKey(Course, null=True, on_delete=models.SET_NULL)
    thesis_required = models.BooleanField(default=False)
    project_required = models.BooleanField(default=False)


class Tracks_in_Major(models.Model):
    major = models.ForeignKey(Major, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    required_gpa = models.FloatField(default=3.0)

    def __str__(self):
        return str(self.major) + ' - ' + str(self.name)


class Student(models.Model):
    sbu_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gpa = models.FloatField(default=4.0)
    email = models.CharField(max_length=100)
    entry_semester_season = models.CharField(max_length=6, choices=Season.choices, default=Season.FALL)
    entry_semester_year = models.IntegerField(default=datetime.now().year)
    graduation_semester_season = models.CharField(max_length=6, choices=Season.choices, default=Season.FALL)
    graduation_semester_year = models.IntegerField(default=datetime.now().year)
    requirement_semester_season = models.CharField(max_length=6, choices=Season.choices, default=Season.FALL)
    requirement_semester_year = models.IntegerField(default=datetime.now().year)
    major = models.ForeignKey(Major, null=True, on_delete=models.SET_NULL)
    track = models.ForeignKey(Tracks_in_Major, null=True, on_delete=models.SET_NULL)
    graduated = models.BooleanField(default=False)
    withdrew = models.BooleanField(default=False)
    satisfied_courses = models.IntegerField(default=0)
    unsatisfied_courses = models.IntegerField(default=0)
    pending_courses = models.IntegerField(default=0)
    # password = models.CharField(max_length=100) # may be unnecessary

    def __str__(self):
        return str(self.sbu_id)


class Classes_Taken_by_Student(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, null=True, on_delete=models.SET_NULL)
    grade = models.CharField(max_length=3, choices=Grade.choices, default=Grade.NOT_APPLICABLE)
    status = models.CharField(max_length=15, choices=CourseStatus.choices, default=CourseStatus.PENDING)

    def __str__(self):
        return str(self.student) + ' - ' + str(self.course)


class Schedule(models.Model):
    student = models.ForeignKey(Student, on_delete = models.CASCADE)
    semesters = models.JSONField()


class Comment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    author = models.CharField(max_length=100, default='no auth')
    text = models.CharField(max_length=1000)
    post_date = models.CharField(max_length=100)