#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: Check the service info files for ucr and the umc services module
## exposure: careful
## tags: [apptest]
## bugs: [50098]

from __future__ import print_function

from univention.service_info import ServiceInfo


def test_check_univention_service():
	services_info = ServiceInfo()
	service_problems = services_info.check_services()
	print('Services with problems:\n{}'.format(service_problems))
	assert len(service_problems) == 0


if __name__ == '__main__':
	test_check_univention_service()
