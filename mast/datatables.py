from .models import Student, Major, Semester
from table import Table
from table.columns import Column


class StudentDatatable(Table):
    sbu_id = Column(field='sbu_id') 
    name = Column(field='last_name')   
    class Meta:
        model = Student
    