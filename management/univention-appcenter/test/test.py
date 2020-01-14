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
	def __init__(self):
		self.conn = sqlite3.connect('apps.db')

	def get_every_single_app(self):
		c = self.conn.cursor()

		for row in c.execute('SELECT attrs FROM apps ORDER BY id, version'):
			app = App(json.loads(row[0]), None)
			yield app

	def get_all_apps_with_id(self, app_id):
		c = self.conn.cursor()

		for row in c.execute("SELECT attrs FROM apps WHERE id = ? ORDER BY id, version", (app_id,)):
			app = App(json.loads(row[0]), None)
			yield app



@profile
def iter_apps():
	apps = Apps().get_every_single_app()
	for app in apps:
		pass



@profile
def iter_apps2():
	apps = Apps2().get_every_single_app()
	for app in apps:
		pass


iter_apps()
iter_apps2()

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

find_samba_with_old_backend()
find_samba_with_sql_backend()



@measure_time
def get_all_apps_with_old_backend(timer):
	for x in xrange(10):
		with timer:
			Apps().get_all_apps()

@measure_time
def get_all_apps_with_sql_backend(timer):
	for x in xrange(10):
		with timer:
			Apps().get_all_apps()

get_all_apps_with_old_backend()
get_all_apps_with_sql_backend()

