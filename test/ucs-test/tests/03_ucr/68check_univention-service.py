#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check the service info files for ucr and the umc services module
## exposure: careful
## tags: [apptest]
## bugs: [50098]

from univention.service_info import ServiceInfo


def test_check_univention_service():
    services_info = ServiceInfo()
    service_problems = services_info.check_services()
    print(f'Services with problems:\n{service_problems}')
    assert len(service_problems) == 0


if __name__ == '__main__':
    test_check_univention_service()
