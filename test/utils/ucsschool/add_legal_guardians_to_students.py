#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from itertools import cycle

from ucsschool.lib.models.school import School
from ucsschool.lib.models.user import LegalGuardian, Student
from univention.admin.uldap import getMachineConnection


# The ratio between students and legal guardians should be chosen such that limits are
# not reached (10 legal wards per guardian or 4 legal guardians per ward).
# Otherwise, this may fail during modification of a student.
# Add 1 legal guardian to each student

lo, _ = getMachineConnection()

for school in School.get_all(lo):
    print(f"Add one legal guardian to each student in {school.name}")
    legal_guardians = LegalGuardian.get_all(lo, school.name)
    if not legal_guardians:
        continue

    cycled_legal_guardians = cycle(legal_guardians)

    for student in Student.get_all(lo, school.name):
        legal_guardian_dn = next(cycled_legal_guardians).dn
        student.legal_guardians = list({legal_guardian_dn}.union(student.legal_guardians or []))
        student.modify(lo)
