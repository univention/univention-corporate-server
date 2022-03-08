from abc import ABC, ABCMeta, abstractmethod
from multiprocessing import Process, current_process
from threading import Thread, current_thread
from typing import Union, Type


class WorkerInfo(object):
	"""
	Immutable class to hold information about current process and thread IDs.
	"""

	def __init__(self):
		"""
		Initializes `WorkerInfo` instance.
		"""
		self.__process_id = current_process().ident
		self.__thread_id = current_thread().ident

	@property
	def process_id(self) -> int:
		"""
		Current process ID.
		"""
		return self.__process_id

	@property
	def thread_id(self) -> int:
		"""
		Current thread ID.
		"""
		return self.__thread_id

	def __str__(self) -> str:
		"""
		String representation of the `WorkerInfo` object.
		"""
		return f"process: {self.process_id}; thread: {self.thread_id}"


class Worker(ABC):
	"""
	Interface worker class that will be used by thread- and process-based subclasses. Can not be instantiated directly.
	"""

	def __init__(self, executor_type: Type[Union[Thread, Process]], name: str = None) -> None:
		"""
		Initializes `Worker` instance.
		"""
		self.__executor = executor_type(target=self.task, name=name)
		self.__running = False

	@property
	def name(self) -> str:
		"""
		Returns name of the worker.
		"""
		return self.__executor.name

	@abstractmethod
	def task(self):
		"""
		Task to be performed.
		"""
		raise NotImplementedError

	def start(self):
		"""
		Start actual work.
		"""
		if self.__running:
			raise RuntimeError("Worker is already running")
		elif not self.__executor:
			raise RuntimeError("No executor set - worker probably already finished")

		try:
			self.__executor.start()
			self.__running = True
		except RuntimeError:
			self.__executor = None
			self.__running = False

	def wait(self, timeout=None):
		"""
		Wait for the work to be completed. Completion does not assume success or failure: both are to be expected.

		:param int timeout: How much time (in milliseconds) to wait for work to be finished. Default is: None.
		"""
		try:
			if self.__running and self.__executor:
				self.__executor.join(timeout)
		finally:
			self.__executor = None
			self.__running = False


class WorkerThread(Worker, metaclass=ABCMeta):
	"""
	Performs given task in separate thread. Can not be instantiated directly.
	"""

	def __init__(self):
		"""
		Initializes `WorkerThread` instance.
		"""
		super(WorkerThread, self).__init__(Thread)


class WorkerProcess(Worker, metaclass=ABCMeta):
	"""
	Performs given task in separate process. Can not be instantiated directly.
	"""

	def __init__(self):
		"""
		Initializes `WorkerProcess` instance.
		"""
		super(WorkerProcess, self).__init__(Process)
