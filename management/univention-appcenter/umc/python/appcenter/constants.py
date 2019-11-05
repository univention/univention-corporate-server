# Base UCR path definitions
ONLINE_BASE = 'repository/online'
COMPONENT_BASE = '%s/component' % ONLINE_BASE

# Parameter names for component definitions
COMP_PARAMS = ['description', 'server', 'prefix', 'password', 'username', 'defaultpackages', 'version', 'localmirror', 'unmaintained']

# Symbolic error codes for UCR write operations
PUT_SUCCESS = 0
PUT_PARAMETER_ERROR = 1  # content of request record isn't valid
PUT_PROCESSING_ERROR = 2  # some error while parameter processing
PUT_WRITE_ERROR = 3  # some error while saving data
PUT_UPDATER_ERROR = 4  # after saving options, any errors related to repositories
PUT_UPDATER_NOREPOS = 5  # nothing committed, but not found any valid repository

STATUS_ICONS = {
	'installed': 'updater-installed',
	'available': 'updater-available',
	'access_denied': 'updater-access-denied'
}
DEFAULT_ICON = 'updater-unknown'  # any states not defined above

COMPATIBILITY_VERSION = '4.4-2 errata312'
