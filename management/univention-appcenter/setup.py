from packaging import setup

setup(name='python-univention-appcenter',
	packages=[
		'univention.appcenter',
		'univention.appcenter.actions',
	],
	package_dir={
		'univention.appcenter': 'python/appcenter',
		'univention.appcenter.actions': 'python/appcenter/actions',
	},
)
