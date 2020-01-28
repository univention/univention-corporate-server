import datetime
import sqlite3
import json

from memory_profiler import profile

from univention.appcenter.app_cache import Apps
from univention.appcenter.app import App

class Timer(object):
	def __init__(self, name):
		self.name = name
		self.results = []
		self.__start = None

	def __enter__(self):
		self.__start = datetime.datetime.now()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		end = datetime.datetime.now()
		self.tick(end - self.__start)
		self.__start = None


	def tick(self, delta):
		self.results.append(delta)

	def print_result(self):
		print('=== {} ==='.format(self.name))
		print('{} result(s)'.format(len(self.results)))
		print('{} total'.format(sum(self.results, datetime.timedelta(0))))
		print('{} avg'.format(sum(self.results, datetime.timedelta(0)) / len(self.results)))

def measure_time(f):
	timer = Timer(f.__name__)
	def _f():
		ret = f(timer)
		timer.print_result()
		return ret
	return _f


# New SQL backend; naive implementation
class Apps2(Apps):
	conn = sqlite3.connect('apps.db')
	cursor = conn.cursor()

	def build_app(self, row):
		return App(json.loads(row[0]), None)

	get_every_single_app_stmt = 'SELECT attrs FROM apps ORDER BY id, version'
	def get_every_single_app(self):
		for row in self.cursor.execute(self.get_every_single_app_stmt):
			app = self.build_app(row)
			yield app

	get_all_apps_with_id_stmt = "SELECT attrs FROM apps WHERE id = ? ORDER BY id, version"
	def get_all_apps_with_id(self, app_id):
		for row in self.cursor.execute(self.get_all_apps_with_id_stmt, (app_id,)):
			app = self.build_app(row)
			yield app

	get_all_locally_installed_apps_stmt = "SELECT attrs FROM apps WHERE installed = 1 ORDER BY id, version"
	def get_all_locally_installed_apps(self):
		for row in self.cursor.execute(self.get_all_locally_installed_apps_stmt):
			app = self.build_app(row)
			yield app


	find_by_component_id_stmt = "SELECT attrs FROM apps WHERE component_id = ?"
	def find_by_component_id(self, component_id):
		row = self.cursor.execute(self.find_by_component_id_stmt, (component_id,)).fetchone()
		if row:
			return self.build_app(row)

# New SQL backend; another naive implementation
ATTRS = []
for attr in sorted(App._attrs, cmp=lambda x, y: cmp(x.name, y.name)):
	ATTRS.append('app_attr_%s' % attr.name)

class Apps3(Apps2):
	def build_app(self, row):
		attrs = {}
		for i, a in enumerate(ATTRS):
			attrs[a[9:]] = row[i]
		return App(attrs, None)

	get_every_single_app_stmt = 'SELECT %s FROM apps ORDER BY id, version' % ', '.join(ATTRS)

@profile
def iter_apps():
	apps = Apps().get_every_single_app()
	for app in apps:
		pass



@profile
def iter_apps2():
	_apps = Apps2()
	apps = _apps.get_every_single_app()
	for app in apps:
		pass


#iter_apps()
#iter_apps2()

@measure_time
def find_samba_with_old_backend(timer):
	for x in xrange(1000):
		with timer:
			Apps().find('samba4')

@measure_time
def find_samba_with_sql_backend(timer):
	for x in xrange(1000):
		with timer:
			Apps2().find('samba4')



@measure_time
def get_every_single_app_with_old_backend(timer):
	for x in xrange(10):
		with timer:
			list(Apps().get_every_single_app())

@measure_time
def get_every_single_app_with_sql_backend(timer):
	for x in xrange(10):
		with timer:
			list(Apps2().get_every_single_app())

@measure_time
def get_every_single_app_with_sql_backend3(timer):
	for x in xrange(10):
		with timer:
			list(Apps3().get_every_single_app())




@measure_time
def get_all_apps_with_old_backend(timer):
	for x in xrange(10):
		with timer:
			Apps().get_all_apps()

@measure_time
def get_all_apps_with_sql_backend(timer):
	for x in xrange(10):
		with timer:
			Apps2().get_all_apps()


# new tests

@measure_time
def get_all_locally_installed_apps_with_old_backend(timer):
	for x in xrange(10):
		with timer:
			list(Apps().get_all_locally_installed_apps())

@measure_time
def get_all_locally_installed_apps_with_sql_backend(timer):
	for x in xrange(10):
		with timer:
			list(Apps2().get_all_locally_installed_apps())


@measure_time
def get_all_apps_with_id_with_old_backend(timer):
	for x in xrange(10):
		with timer:
			list(Apps().get_all_apps_with_id('samba4'))

@measure_time
def get_all_apps_with_id_with_sql_backend(timer):
	for x in xrange(10):
		with timer:
			list(Apps2().get_all_apps_with_id('samba4'))



@measure_time
def find_component_id_with_old_backend(timer):
	for x in xrange(10):
		with timer:
			Apps().find_by_component_id('samba4')

@measure_time
def find_component_id_with_sql_backend(timer):
	for x in xrange(10):
		with timer:
			Apps2().find_by_component_id('samba4')


@measure_time
def find_candidate_with_old_backend(timer):
	app = Apps().find('nextcloud')
	for x in xrange(10):
		with timer:
			Apps().find_candidate(app)

@measure_time
def find_candidate_with_sql_backend(timer):
	app = Apps2().find('nextcloud')
	for x in xrange(10):
		with timer:
			Apps2().find_candidate(app)

find_samba_with_old_backend()
find_samba_with_sql_backend()
print('')
get_every_single_app_with_old_backend()
get_every_single_app_with_sql_backend()
get_every_single_app_with_sql_backend3()
print('')
get_all_apps_with_old_backend()
get_all_apps_with_sql_backend()
print('')
get_all_locally_installed_apps_with_old_backend()
get_all_locally_installed_apps_with_sql_backend()
print('')
get_all_apps_with_id_with_old_backend()
get_all_apps_with_id_with_sql_backend()
print('')
find_component_id_with_old_backend()
find_component_id_with_sql_backend()
print('')
find_candidate_with_old_backend()
find_candidate_with_sql_backend()

