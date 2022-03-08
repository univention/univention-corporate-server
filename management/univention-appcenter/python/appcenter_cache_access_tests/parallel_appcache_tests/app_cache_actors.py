import json
from contextlib import contextmanager
from multiprocessing import Process, Queue, Lock as ProcessLock
from pathlib import Path
from threading import Thread, Lock as ThreadLock
from time import sleep
from typing import Type, Union

from parallel_appcache_tests.workers import Worker, WorkerInfo

thread_lock = ThreadLock()
process_lock = ProcessLock()


class AppCacheActor(Worker):

	def __init__(self, executor_type: Type[Union[Thread, Process]], file_path: Path, results: Queue, name: str = None):
		super().__init__(executor_type=executor_type, name=name)
		self.__file_path = file_path
		self.__results = results
		self.__command = Queue()
		self.__parent_info = WorkerInfo()
		self._lock = False

	def signal(self, command: str = None):
		self.__command.put(command)

	def _write(self, info: WorkerInfo) -> dict:
		data = {"pid": info.process_id, "tid": info.thread_id, "wid": self.name}
		with open(self.__file_path, 'w') as fd:
			json.dump(data, fd)

		return data

	def _read(self) -> dict:
		data = {}
		try:
			with open(self.__file_path) as fd:
				data = json.load(fd)
		except Exception:
			pass

		return {"pid": data.get("pid"), "tid": data.get("tid"), "wid": data.get("wid")}

	@contextmanager
	def _spinlock(self):
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

	@contextmanager
	def _threadlock(self):
		global thread_lock

		lock = thread_lock

		try:
			lock.acquire()
			yield lock
		finally:
			try:
				if lock:
					lock.release()
			except:
				pass

	@contextmanager
	def _processlock(self):
		global process_lock

		lock = process_lock

		try:
			lock.acquire()
			yield lock
		finally:
			try:
				if lock:
					lock.release()
			except:
				pass

	def task(self):
		info = WorkerInfo()
		written = None

		with self._spinlock():
			while True:
				command = self.__command.get()
				if command == "read":
					read = self._read()
					result = (read == written)
					print(f"worker: {self.name}, result: {result}")
					self.__results.put(result)
				elif command == "write":
					written = self._write(info)
				elif command in ['q', 'quit', 'exit']:
					print(f"Exiting: {self.name}")
					break


class AppCacheActorThread(AppCacheActor):

	def __init__(self, file_path: Path, results: Queue, name: str = None):
		super().__init__(executor_type=Thread, file_path=file_path, results=results, name=name)


class AppCacheActorProcess(AppCacheActor):

	def __init__(self, file_path: Path, results: Queue, name: str = None):
		super().__init__(executor_type=Process, file_path=file_path, results=results, name=name)
