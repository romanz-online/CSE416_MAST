from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Semester, Season


@login_required
def rollover_semester_page(request):
    if request.user.groups.filter(name='Student'):
        return render(request, 'mast/home.html', {None: None})

    current_semester = Semester.objects.filter(is_current_semester=True)[0]
    next_year = current_semester.year
    if current_semester.season == Season.WINTER:
        next_season = Season.SPRING
    elif current_semester.season == Season.SPRING:
        next_season = Season.SUMMER
    elif current_semester.season == Season.SUMMER:
        next_season = Season.FALL
    else:
        next_season = Season.WINTER
        next_year += 1

    next_semester = Semester.objects.filter(season=next_season, year=next_year)[0]

    return render(request, 'mast/rollover_semester.html', {
        'current_semester': current_semester,
        'next_semester': next_semester,
    })


@login_required
def rollover_semester(request):
    current_semester = Semester.objects.filter(is_current_semester=True)[0]
    next_year = current_semester.year
    if current_semester.season == Season.WINTER:
        next_season = Season.SPRING
    elif current_semester.season == Season.SPRING:
        next_season = Season.SUMMER
    elif current_semester.season == Season.SUMMER:
        next_season = Season.FALL
    else:
        next_season = Season.WINTER
        next_year += 1

    next_semester = Semester.objects.filter(season=next_season, year=next_year)[0]

    return rollover_semester_page(request)