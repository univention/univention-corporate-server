#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import argparse
from itertools import cycle

from ucsschool.lib.models.group import WorkGroup
from ucsschool.lib.models.user import Student
from univention.admin.uldap import getMachineConnection


parser = argparse.ArgumentParser()
parser.add_argument('school', nargs='+', type=str)
parser.add_argument('--workgroup-count', default=10, type=int)
parser.add_argument('--student-count', default=20, type=int)
args = parser.parse_args()

lo, _ = getMachineConnection()

for school_name in args.school:
    print(f'Creating {args.workgroup_count} work groups in {school_name} with {args.student_count} students each.')
    students = cycle([student.dn for student in Student.get_all(lo, school_name)])
    for wg_id in range(args.workgroup_count):
        wg = WorkGroup(f'{school_name}-wg{wg_id}', school_name)
        wg.users = [next(students) for _ in range(args.student_count)]
        wg.create(lo)
