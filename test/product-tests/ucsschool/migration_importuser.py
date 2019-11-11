#!/usr/bin/env python2

from ucsschool.lib.models import Student
from univention.admin.uldap import getAdminConnection
import sys

lo, po = getAdminConnection()

student = Student(name='Teststudent', firstname='Test', lastname='Student', school='School1')
student.create(lo)

student2 = Student(name='Teststudent2', firstname='Test2', lastname='Student2', school='School2')
student2.create(lo)

student3 = Student(name='Teststudent3', firstname='Test3', lastname='Student3', school='School1', schools=['School1', 'School2'])
student3.create(lo)

s = lo.get(student.dn)
if ['School1'] != s['ucsschoolSchool']:
    print('Error: Student should only be in School1')
    sys.exit(1)

s2 = lo.get(student2.dn)
if ['School2'] != s2['ucsschoolSchool']:
    print('Error: Student should only be in School2')
    sys.exit(1)

s3 = lo.get(student3.dn)
if set(['School1', 'School2']) != set(s3['ucsschoolSchool']):
    print('Error: Student should be in School1 and School2')
    sys.exit(1)

sys.exit(0)
