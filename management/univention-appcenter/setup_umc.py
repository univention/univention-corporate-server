from distutils.core import setup

setup(name='univention-management-console-modules-appcenter',
    packages=[
	'univention.appcenter.actions',
	],
    package_dir={
	'univention.appcenter.actions': 'python/appcenter-umc/actions',
	},
)
