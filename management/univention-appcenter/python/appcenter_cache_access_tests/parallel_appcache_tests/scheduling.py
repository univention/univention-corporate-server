from collections import OrderedDict


class Schedule(object):

	def __init__(self, wid: int, timestamp: float, command: str):
		self.__wid = wid
		self.__timestamp = timestamp
		self.__command = command

	@property
	def wid(self) -> int:
		return self.__wid

	@property
	def timestamp(self) -> float:
		return self.__timestamp

	@property
	def command(self) -> str:
		return self.__command

	def __str__(self):
		return f"wid={self.wid}\ttimestamp={self.timestamp}\tcommand={self.command}"


def generate_schedule(worker_count: int, period: float) -> OrderedDict:
	schedules = dict()
	for n in range(1, worker_count + 1):
		write_ts = (n - 1) * period
		if write_ts in schedules:
			schedules[write_ts].append((n, "write"))
		else:
			schedules[write_ts] = [(n, "write")]

		read_ts = (n + 1) * period
		if read_ts in schedules:
			schedules[read_ts].append((n, "read"))
		else:
			schedules[read_ts] = [(n, "read")]

	return OrderedDict(sorted(schedules.items()))
