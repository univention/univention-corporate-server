# shared\_memory

As shared memory was introduced in Python 3.8 we need to backport it for Python 3.7 (UCS 5.0) and Python 2.7 (UCS 4.4).

The original sources are copied from:
[Modules/_multiprocessing/posixshmem.c](https://github.com/python/cpython/blob/main/Modules/_multiprocessing/posixshmem.c)
[Modules/_multiprocessing/clinic/posixshmem.c.h](https://github.com/python/cpython/blob/main/Modules/_multiprocessing/clinic/posixshmem.c.h)
[Lib/multiprocessing/shared\_memory.py](https://github.com/python/cpython/blob/main/Lib/multiprocessing/shared_memory.py)
