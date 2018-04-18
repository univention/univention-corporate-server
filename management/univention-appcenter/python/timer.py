#
# Use: print("\n".join(timer.sprint_timer_total()))
#
# To time app center cache rebuild:
#
# rm /var/cache/univention-appcenter/appcenter-test.software-univention.de/4.?/.apps.*.json
# python -c 'import time; from univention.appcenter.app_cache import Apps, AppCenterCache, timer; t1 = time.time(); print("** len(apps)={}".format(len(Apps().get_all_apps()))); t2 = time.time() - t1; app_caches = dict((ac.get_ucs_version(), ac) for ac in AppCenterCache().get_app_caches()); print("** app cache entries: {!r}".format(dict((ac.get_ucs_version(), len(ac._cache)) for ac in app_caches.values()))); print("\n".join(timer.sprint_timer_total())); print("** Time: {}".format(t2))'
#

import time
from collections import OrderedDict


class Timer(object):
	def __init__(self):
		self.timer_one = OrderedDict()
		self.timer_total = OrderedDict()
		self.timer_last = 0.0

	def add_timing(self, name):
		now = time.time()
		if not self.timer_last:
			self.timer_last = now
		time_diff = now - self.timer_last
		self.timer_last = now
		self.timer_one[name] = time_diff
		try:
			self.timer_total[name] += time_diff
		except KeyError:
			self.timer_total[name] = time_diff

	def reset_timer(self):
		self.timer_one.clear()
		self.timer_last = 0.0

	def sprint_timer_one(self):
		return self._sprint_timer(self.timer_one)

	def sprint_timer_total(self):
		return self._sprint_timer(self.timer_total)

	@staticmethod
	def _sprint_timer(timer):
		res = []
		key_len = max(len(k) for k in timer.keys())
		template = '{:_<%d}: {:f}' % (key_len,)
		for name, time_diff in timer.items():
			res.append(template.format(name, time_diff))
		return res
