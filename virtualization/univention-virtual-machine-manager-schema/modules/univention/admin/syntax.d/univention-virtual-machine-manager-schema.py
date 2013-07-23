class UvmmProfiles(UDM_Objects):
	description = _('UVMM: Profile')
	udm_modules = ('uvmm/profile',)
	key = 'dn'
	label = '%(name)s'
	empty_value = True
	simple = True
	use_objects = False
