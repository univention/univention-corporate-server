from packaging import setup

setup(name='univention-management-console-module-appcenter',
	packages=[
		'univention.appcenter.actions',
	],
	package_dir={
		'univention.appcenter.actions': 'python/appcenter-umc/actions',
	},
)
