from multiprocessing import Queue
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Event
from time import perf_counter
from typing import List, Tuple, Type, Union
from uuid import uuid4

import pytest

from parallel_appcache_tests.app_cache_actors import AppCacheActorThread, AppCacheActorProcess
from parallel_appcache_tests.scheduling import generate_schedule
from parallel_appcache_tests.workers import WorkerInfo


def _sort_force_write(actions: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
	"""
	Input actions are in form of: [(2, "read"), (4, "write")]. Order list in such way that items with second tuple
	value (action) set to "write" are listed first
	"""
	actions.sort(key=lambda x: x[1], reverse=True)

	return actions


def _sort_force_read(actions: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
	"""
	Input actions are in form of: [(2, "read"), (4, "write")]. Order list in such way that items with second tuple
	value (action) set to "read" are listed first
	"""
	actions.sort(key=lambda x: x[1])

	return actions


def _dump_results_queue(q: Queue) -> List[bool]:
	"""
	Convert Queue to list
	"""
	q.put(None)
	return list(iter(q.get, None))


def _execute(actor: Type[Union[AppCacheActorThread, AppCacheActorProcess]], worker_count: int, period: float, force_write: bool=True) -> List[bool]:
	event = Event()
	results = Queue()
	actors = [actor(file_path=Path('/tmp/app_cache.json'), results=results) for it in range(0, worker_count)]
	for actor in actors:
		actor.start()

	start_time = 0.0
	schedules = generate_schedule(worker_count=worker_count, period=period)
	for key, val in schedules.items():
		delay = key - start_time
		start_time = key
		event.wait(timeout=delay)
		actions = _sort_force_write(val) if force_write else _sort_force_read(val)
		for action in actions:
			wid = action[0] - 1
			command = action[1]
			actors[wid].signal(command)

	for actor in actors:
		actor.signal("exit")
		actor.wait()

	return _dump_results_queue(results)


def _file_rw_timing(iter_count: int = 1000) -> float:
	"""
	Perform write and read on many files and pick the longest time.
	"""
	info = WorkerInfo()
	data = {"pid": info.process_id, "tid": info.thread_id, "rnd": ""}

	results = []
	read = []
	for it in range(0, iter_count):
		begin_time = perf_counter()
		data["rnd"] = uuid4()
		with NamedTemporaryFile(mode="w+") as fdw:
			fdw.write(str(data))
			fdw.flush()

			with open(fdw.name, mode="r") as fdr:
				read.append(fdr.read())
		end_time = perf_counter()
		results.append(end_time - begin_time)

	return max(results)


@pytest.fixture(scope="session", params=[2.0])
def period(request):
	"""
	Recalculate period if needed, say if RW file timing is greater than 10% of given period
	"""
	rw_timing = _file_rw_timing()
	period = float(request.param)
	if rw_timing > period / 10.0:
		period = 100 * rw_timing

	yield period


@pytest.mark.parametrize('worker_count', [5])
def test_thread_workers_spinlock_force_write(period, worker_count):
	"""
	Multiple simultaneous/overlapping thread-based workers. Use current spinlock implementation from AppCache.
	It is expected only the last of the results is True, meaning it is the only case there were no results overriding.
	"""

	expected_results = [False] * (worker_count - 1) + [True]
	results = _execute(actor=AppCacheActorThread, worker_count=worker_count, period=period, force_write=True)

	assert results == expected_results, "race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_thread_workers_spinlock_force_read(period, worker_count):
	"""
	Multiple simultaneous/overlapping thread-based workers. Use current spinlock implementation from AppCache.
	It is expected only the last of the results is True, meaning it is the only case there were no results overriding.
	"""

	expected_results = [False] * (worker_count - 1) + [True]
	results = _execute(actor=AppCacheActorThread, worker_count=worker_count, period=period, force_write=False)

	assert results == expected_results, "race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_process_workers_spinlock_force_write(period, worker_count):
	"""
	Multiple simultaneous/overlapping process-based workers. Use current spinlock implementation from AppCache.
	It is expected only the last of the results is True, meaning it is the only case there were no results overriding.
	"""

	expected_results = [False] * (worker_count - 1) + [True]
	results = _execute(actor=AppCacheActorProcess, worker_count=worker_count, period=period, force_write=True)

	assert results == expected_results, "race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_process_workers_spinlock_force_read(period, worker_count):
	"""
	Multiple simultaneous/overlapping process-based workers. Use current spinlock implementation from AppCache.
	It is expected only the last of the results is True, meaning it is the only case there were no results overriding.
	"""

	expected_results = [False] * (worker_count - 1) + [True]
	results = _execute(actor=AppCacheActorProcess, worker_count=worker_count, period=period, force_write=False)

	assert results == expected_results, "race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_thread_workers_threadlock_force_write(monkeypatch, period, worker_count):
	"""
	Multiple simultaneous/overlapping thread-based workers. Use thread-lock.
	It is expected all result values are True, meaning synchronization is working as expected.
	"""

	expected_results = [True] * worker_count
	with monkeypatch.context() as mp:
		mp.setattr("parallel_appcache_tests.app_cache_actors.AppCacheActorThread._spinlock", AppCacheActorThread._threadlock, raising=True)
		results = _execute(actor=AppCacheActorThread, worker_count=worker_count, period=period, force_write=True)

	assert results == expected_results, "no race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_thread_workers_threadlock_force_read(monkeypatch, period, worker_count):
	"""
	Multiple simultaneous/overlapping thread-based workers. Use thread-lock.
	It is expected all result values are True, meaning synchronization is working as expected.
	"""

	expected_results = [True] * worker_count
	with monkeypatch.context() as mp:
		mp.setattr("parallel_appcache_tests.app_cache_actors.AppCacheActorThread._spinlock", AppCacheActorThread._threadlock, raising=True)
		results = _execute(actor=AppCacheActorThread, worker_count=worker_count, period=period, force_write=False)

	assert results == expected_results, "no race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_thread_workers_processlock_force_write(monkeypatch, period, worker_count):
	"""
	Multiple simultaneous/overlapping thread-based workers. Use process-lock.
	It is expected all result values are True, meaning synchronization is working as expected.
	"""

	expected_results = [True] * worker_count
	with monkeypatch.context() as mp:
		mp.setattr("parallel_appcache_tests.app_cache_actors.AppCacheActorThread._spinlock", AppCacheActorThread._processlock, raising=True)
		results = _execute(actor=AppCacheActorThread, worker_count=worker_count, period=period, force_write=True)

	assert results == expected_results, "no race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_thread_workers_processlock_force_read(monkeypatch, period, worker_count):
	"""
	Multiple simultaneous/overlapping thread-based workers. Use process-lock.
	It is expected all result values are True, meaning synchronization is working as expected.
	"""

	expected_results = [True] * worker_count
	with monkeypatch.context() as mp:
		mp.setattr("parallel_appcache_tests.app_cache_actors.AppCacheActorThread._spinlock", AppCacheActorThread._processlock, raising=True)
		results = _execute(actor=AppCacheActorThread, worker_count=worker_count, period=period, force_write=False)

	assert results == expected_results, "no race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_process_workers_threadlock_force_write(monkeypatch, period, worker_count):
	"""
	Multiple simultaneous/overlapping process-based workers. Use thread-lock.
	It is expected only the last of the results is True, meaning it is the only case there were no results overriding.
	"""

	expected_results = [False] * (worker_count - 1) + [True]
	with monkeypatch.context() as mp:
		mp.setattr("parallel_appcache_tests.app_cache_actors.AppCacheActorProcess._spinlock", AppCacheActorProcess._threadlock, raising=True)
		results = _execute(actor=AppCacheActorProcess, worker_count=worker_count, period=period, force_write=True)

	assert results == expected_results, "race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_process_workers_threadlock_force_read(monkeypatch, period, worker_count):
	"""
	Multiple simultaneous/overlapping process-based workers. Use thread-lock.
	It is expected only the last of the results is True, meaning it is the only case there were no results overriding.
	"""

	expected_results = [False] * (worker_count - 1) + [True]
	with monkeypatch.context() as mp:
		mp.setattr("parallel_appcache_tests.app_cache_actors.AppCacheActorProcess._spinlock", AppCacheActorProcess._threadlock, raising=True)
		results = _execute(actor=AppCacheActorProcess, worker_count=worker_count, period=period, force_write=False)

	assert results == expected_results, "race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_process_workers_processlock_force_write(monkeypatch, period, worker_count):
	"""
	Multiple simultaneous/overlapping process-based workers. Use thread-lock.
	It is expected all result values are True, meaning synchronization is working as expected.
	"""

	expected_results = [True] * worker_count
	with monkeypatch.context() as mp:
		mp.setattr("parallel_appcache_tests.app_cache_actors.AppCacheActorProcess._spinlock", AppCacheActorProcess._processlock, raising=True)
		results = _execute(actor=AppCacheActorProcess, worker_count=worker_count, period=period, force_write=True)

	assert results == expected_results, "no race condition triggered"


@pytest.mark.parametrize('worker_count', [5])
def test_process_workers_processlock_force_read(monkeypatch, period, worker_count):
	"""
	Multiple simultaneous/overlapping process-based workers. Use thread-lock.
	It is expected all result values are True, meaning synchronization is working as expected.
	"""

	expected_results = [True] * worker_count
	with monkeypatch.context() as mp:
		mp.setattr("parallel_appcache_tests.app_cache_actors.AppCacheActorProcess._spinlock", AppCacheActorProcess._processlock, raising=True)
		results = _execute(actor=AppCacheActorProcess, worker_count=worker_count, period=period, force_write=False)

	assert results == expected_results, "no race condition triggered"
