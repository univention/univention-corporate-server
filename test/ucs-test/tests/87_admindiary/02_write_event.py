#!/usr/share/ucs-test/runner /usr/bin/py.test-3 -s
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
from univention.testing import utils


def test_write_event():
	with udm_test.UCSTestUDM() as udm, ucr_test.UCSTestConfigRegistry() as ucr, univention.admindiary.backend.get_client(version=1) as client:
		dn, username = udm.create_user()
		expected = {'id': 33, 'date': datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S'), 'event_name': 'UDM_USERS_USER_CREATED', 'hostname': ucr['hostname'], 'username': 'cn=admin', 'message': None, 'args': {'username': username, 'module': 'users/user'}, 'comments': False}
		utils.wait_for_replication()
		entries = [_ for _ in client.query() if _['event_name'] == 'UDM_USERS_USER_CREATED']
		x = entries[-1]
		expected['id'] = x['id']
		expected['date'] = x['date']
		expected['context_id'] = x['context_id']
		assert x == expected
