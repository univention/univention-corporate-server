from univention.management.console import Translation
from univention.management.console.base import Base, UMC_Error
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules.sanitizers import IntegerSanitizer
from univention.management.console.modules.decorators import sanitize

_ = Translation('univention-management-console-modules-udm').translate


class Instance(Base):

	def init(self):
		"""Initialize the module with some values"""
		super(Instance, self).init()
		self.data = [int(x) for x in ucr.get('some/examle/ucr/variable', '1,2,3').split(',')]

	def query(self, request):
		"""get all values of self.data"""
		self.finished(request.id, self.data)

	@sanitize(item=IntegerSanitizer(required=True))
	def get(self, request):
		"""get a specific item of self.data"""
		try:
			item = self.data[request.options['item']]
		except IndexError:
			MODULE.error('A invalid item was accessed.')
			raise UMC_Error(_('The item %d does not exists.') % (request.options['item'],), status=400)
		self.finished(request.id, self.data[item])

	@sanitize(IntegerSanitizer(required=True))
	def put(self, request):
		"""replace all data with the list provided in request.options"""
		self.data = request.options
		self.finished(request.id, None)
