from distutils.core import setup

setup(name='univention-appcenter',
    packages=[
	'univention.appcenter',
	'univention.appcenter.actions',
	],
    package_dir={
	'univention.appcenter': 'python/appcenter',
	'univention.appcenter.actions': 'python/appcenter/actions',
	},
)
