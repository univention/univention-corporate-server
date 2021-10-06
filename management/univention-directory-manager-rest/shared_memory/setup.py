from distutils.core import setup, Extension

setup(
	name='posixshmem',
	version='2.0.0',
	description='posixshmem backport of Python 3.8',
	py_modules=['multiprocessing_shared_memory', 'multiprocessing_resource_tracker'],
	ext_modules=[Extension(
		'_posixshmem',
		define_macros=[('HAVE_SHM_OPEN', '1'), ('HAVE_SHM_UNLINK', '1'), ('HAVE_SYS_MMAN_H', '1')],
		libraries=['rt'],
		sources=['posixshmem.c']
	)],
)
