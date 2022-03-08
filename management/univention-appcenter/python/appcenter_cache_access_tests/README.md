# Intro

Goal of the code in this repository is to **try** helping to improve AppCache current issue(s) regarding multiple, 
simultaneous access from different Python/console processes. Since AppCache is not a *service*, access of multiple 
processes which can do both reading and changing content of the files in the underlying operating system.

Current *locking* implementation in AppCache is as follows:
```python
@contextmanager
def _locked(self):
    timeout = 60
    wait = 0.1
    while self._lock:
        if timeout < 0:
            raise RuntimeError('Could not get lock in %s seconds' % timeout)
        sleep(wait)
        timeout -= wait
    self._lock = True
    try:
        yield
    finally:
        self._lock = False
```

# Workers

There are two type of workers:
* thread-based
* process-based

Implementation for both can be found [here](parallel_appcache_tests/workers.py). Base, abstract class is *Worker* 
controlling execution of *task* method in thread or process. All concrete sub-classes have to implement this method.

# Overlapped access

In order to test as many possible combinations, there has to be some form of *scheduling* which will enforce 
overlapping of workers in controlled and repeatable manner. Note, that this is not quite the same as in *real* 
use-case, however it should suffice: basic idea is that workers overlaps while accessing the shared resource. In our 
case, shared resource will be a simple JSON file for which workers contest. At the very beginning, each worker first 
writes content to a file which is "unique" for it (contains process ID, thread ID and unique name of the worker). After 
some "pause", worker will read the content of the file again and compare read content with what it wrote earlier. If 
those two differ, it can only mean that some other worker in the meantime changed the content.

Graphically, this can be depicted as follows:
![](doc/overlap.svg?raw=true)

# Scheduling

Scheduling read/write access is quite simple: we need a "driver" to create and execute schedule, which consists out of: 
**pause** (float value in seconds, how much time to wait before executing next schedule in list) and list of 2-member 
tuples (first member is index of a worker on which to execute command, and second tuple member is the command itself). 
Possible commands sent to worker are:
* write
* read
* exit

Implementation is located [here](parallel_appcache_tests/scheduling.py)

This is how typical schedule generation code looks like:
```python
for delay, schedules in generate_schedule(worker_count=5, period=2.0).items():
	print(f"{delay:0.4f}\t{schedules}")
```

producing the output:
```shell
0.0000	[(1, 'write')]
2.0000	[(2, 'write')]
4.0000	[(1, 'read'), (3, 'write')]
6.0000	[(2, 'read'), (4, 'write')]
8.0000	[(3, 'read'), (5, 'write')]
10.0000	[(4, 'read')]
12.0000	[(5, 'read')]
```

So after given pause (in this case it's 2.0 seconds periodically) there is a list of commands to be executed on given 
workers: some will write and some will read file. There is a possibility to force *write* commands using sorting function:
```python
def _sort_force_write(actions: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
	"""
	Input actions are in form of: [(2, "read"), (4, "write")]. Order list in such way that items with second tuple
	value (action) set to "write" are listed first
	"""
	actions.sort(key=lambda x: x[1], reverse=True)

	return actions
```

This is used in actual tests.

# Testing

Tests are located [here](parallel_appcache_tests/test_cases.py) and AppCache "double" [here](parallel_appcache_tests/app_cache_actors.py).
Basic idea is to first perform some R/W on temporary files, just to see is it fast enough, or better say - does R/W in 
worst case lasts less than 10% of given period (which is 2.0 seconds by default). This is done only once when tests are 
started (thus the "session" scope).

We tried to test the following, using force write and read for each:
* Current ("spinlock") with multiple threads. Race condition *is* expected.
* Current ("spinlock") with multiple processes. Race condition *is* expected.
* Lock from threading, with multiple threads. Race condition *is NOT* expected.
* Lock from multiprocessing, with multiple threads. Race condition *is NOT* expected.
* Lock from threading, with multiple processes. Race condition *is* expected.
* Lock from multiprocessing, with multiple processes. Race condition *is NOT* expected.
