#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: Tests the Univention Admin Diary
## tags: [apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-admin-diary-backend

import datetime

import univention.admindiary.backend
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test


def test_write_event():
	with udm_test.UCSTestUDM() as udm, ucr_test.UCSTestConfigRegistry() as ucr, univention.admindiary.backend.get_client(version=1) as client:
		d = (datetime.datetime.now() - datetime.timedelta(seconds=5)).isoformat()
		dn, username = udm.create_user()
		expected = {
			'id': 33,
			'date': datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S'),
			'event_name': 'UDM_USERS_USER_CREATED',
			'hostname': ucr['hostname'],
			'username': 'cn=admin',
			'message': None,
			'args': {'username': username, 'module': 'users/user'},
			'comments': False
		}
		entries = client.query(d, event='UDM_USERS_USER_CREATED')
		# It is not possible to filter by args in query so we use list comprehension
		x = [entry for entry in entries if entry.get('args', {}).get('username') == username][0]
		assert x is not None
		expected['id'] = x['id']
		expected['date'] = x['date']
		expected['context_id'] = x['context_id']
		assert x == expected
