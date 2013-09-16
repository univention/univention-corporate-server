from univention.lib.i18n import Translation
from univention.management.console.modules import UMC_OptionTypeError
from univention.management.console.modules.decorators import simple_response

_ = Translation( 'univention-management-console' ).translate

class Progress(object):
	def __init__(self, progress_id, title, total):
		self.id = progress_id
		self.title = title
		self.message = ''
		self.current = 0.0
		self.total = total
		self.intermediate = []
		self.finished = False

	def progress(self, detail=None, message=None):
		self.current += 1
		self.intermediate.append(detail)
		if message is not None:
			self.message = message

	def finish(self):
		if self.finished:
			return
		self.finished = True

	def initialised(self):
		return {'id' : self.id, 'title' : self.title}

	def poll(self):
		ret = {
			'title' : self.title,
			'finished' : self.finished,
			'intermediate' : self.intermediate[:],
			'message' : self.message,
			'percentage' : self.current / self.total * 100
		}
		del self.intermediate[:]
		return ret

class EnableProgress(object):
	def new_progress(self, title, total):
		if not hasattr(self, '_progress_id'):
			self._progress_id = 0
		if not hasattr(self, '_progresses'):
			self._progresses = {}
		self._progress_id += 1
		self._progresses[self._progress_id] = progress = Progress(self._progress_id, title, total)
		return progress

	@simple_response
	def progress(self, progress_id):
		if not hasattr(self, '_progresses'):
			self._progresses = {}
		try:
			return self._progresses[progress_id].poll()
		except KeyError:
			raise UMC_OptionTypeError( _( 'Invalid progress ID' ) )

