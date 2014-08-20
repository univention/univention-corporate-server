class UvmmProfiles(UDM_Objects):
	description = _('UVMM: Profile')
	udm_modules = ('uvmm/profile',)
	label = '%(name)s (%(virttech)s)'
	empty_value = True
	use_objects = False

class UvmmCapacity(simple):
	min_length = 1
	max_length = 0
	regex = re.compile(r'^([0-9]+(?:[,.][0-9]+)?)[ \t]*(?:([KkMmGgTtPp])(?:[Ii]?[Bb])?|[Bb])?$')
	error_message = _("Value must be an positive capacity (xx.x [kmgtp][[i]B])")

class UvmmCloudType(UDM_Objects):
	description = _('UVMM: Cloud Types')
	udm_modules = ('uvmm/cloudtype',)
	label = '%(name)s'
	use_objects = False
