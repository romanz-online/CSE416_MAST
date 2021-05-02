import matplotlib
import matplotlib.pyplot as plt
import io
import urllib, base64

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Major, CoursesTakenByStudent, Semester

matplotlib.use('Agg')


@login_required
def enrollment_trends(request):
    if request.user.groups.filter(name='Student'):
        return render(request, 'mast/home.html', {None: None})

    semesters = Semester.objects.order_by('year')
    major_list = Major.objects.order_by('name')

    all_courses_taken = CoursesTakenByStudent.objects.order_by('course')

    X = []
    Y = []
    for course in all_courses_taken:
        if course.course and course.course.course:
            course_string = str(course.course.course)
            if course_string in X:
                Y_index = X.index(course_string)
                Y[Y_index] += 1
            else:
                X += [course_string]
                Y += [1]

    fig = plt.figure()
    plt.bar(X, Y)
    plt.title(
        "Enrollment Trends for all departments from " + str(semesters[0].season) + " " + str(semesters[0].year) + " to "
        + str(semesters[len(semesters) - 1].season) + " " + str(semesters[len(semesters) - 1].year), fontsize=10)
    plt.xlabel("Courses Taken")
    plt.ylabel("Enrollment Count")
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    return render(request, 'mast/enrollment_trends.html',
                  {'semesters': semesters, 'major_list': major_list, 'graph': uri})


@login_required
def enrollment_trends_specify(request):
    if request.user.groups.filter(name='Student'):
        return render(request, 'mast/home.html', {None: None})

    s1 = request.GET['s1']
    s2 = request.GET['s2']
    major = request.GET['major']

    s1_object = Semester.objects.filter(id=s1)[0]
    s2_object = Semester.objects.filter(id=s2)[0]
    major_object = Major.objects.filter(id=major)[0]

    semesters = Semester.objects.order_by('year')
    major_list = Major.objects.order_by('name')

    all_courses_taken = CoursesTakenByStudent.objects.order_by('course')

    # spring 0 # summer 1 # fall 2 # winter 3
    season_dict = {"Spring": 0, "Summer": 1, "Fall": 2, "Winter": 3}

    X = []
    Y = []
    for course in all_courses_taken:
        current_year = course.course.semester.year
        current_season = course.course.semester.season
        if course.student.major == major_object or major_object.department == "N/A":
            if s1_object.year <= current_year <= s2_object.year:
                if (s1_object.year == current_year and season_dict[s1_object.season] > season_dict[current_season]) or \
                        (s2_object.year == current_year) and season_dict[s2_object.season] < season_dict[
                    current_season]:
                    continue
                course_string = str(course.course.course.department) + " " + str(course.course.course.number)
                if course_string in X:
                    Y_index = [X.index(course_string)]
                    Y[Y_index] += 1
                else:
                    X += [course_string]
                    Y += [1]

    fig = plt.figure()
    plt.bar(X, Y)

    title_string = "Enrollment Trends for "
    if major_object.department == "N/A":
        title_string += "all departments from "
    else:
        title_string += major_object.department + " "
    if s1_object != s2_object:
        title_string += "from " + str(s1_object.season) + " " + str(s1_object.year) + " to " + str(s2_object.season) \
                        + " " + str(s2_object.year)
    else:
        title_string += "in " + str(s1_object.season) + " " + str(s1_object.year)

    plt.title(title_string, fontsize=10)
    plt.xlabel("Courses Taken")
    plt.ylabel("Enrollment Count")
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)

    return render(request, 'mast/enrollment_trends.html',
                  {'semesters': semesters, 'major_list': major_list, 'graph': uri, 's1': int(s1), 's2': int(s2),
                   'major_trend': int(major)})
