from distutils.core import setup

setup(name='univention-appcenter-dev',
	packages=[
		'univention.appcenter.actions',
	],
	package_dir={
		'univention.appcenter.actions': 'python/appcenter-dev/actions',
	},
)
