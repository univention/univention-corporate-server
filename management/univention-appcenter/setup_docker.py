from packaging import setup

setup(name='univention-appcenter-docker',
	packages=[
		'univention.appcenter',
		'univention.appcenter.actions',
	],
	package_dir={
		'univention.appcenter': 'python/appcenter-docker',
		'univention.appcenter.actions': 'python/appcenter-docker/actions',
	},
)
