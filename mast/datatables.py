from .models import Student, Course
from table import Table
from table.columns import Column


class StudentDatatable(Table):
    sbu_id = Column(field='sbu_id')
    name = Column(field='last_name')

    class Meta:
        model = Student


class CourseDatatable(Table):
    name = Column(field='name')
    start = Column(field='time_start')

    class Meta:
        model = Course