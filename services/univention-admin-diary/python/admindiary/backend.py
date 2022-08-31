#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from contextlib import contextmanager
from datetime import datetime  # noqa: F401
from functools import partial
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Set, Tuple  # noqa: F401

import sqlalchemy
from sqlalchemy import or_, and_
from sqlalchemy.orm import sessionmaker, relationship, scoped_session, joinedload
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Sequence, Text, DateTime, func, Table

from univention.config_registry import ConfigRegistry

from univention.admindiary import get_logger, DiaryEntry  # noqa: F401

get_logger = partial(get_logger, 'backend')


def get_query_limit():
	# type: () -> int
	ucr = ConfigRegistry()
	ucr.load()
	limit = ucr.get('admin/diary/query/limit', '')
	default_limit = 1000
	try:
		limit = int(limit)
	except ValueError:
		limit = default_limit
	else:
		if limit < 0:
			limit = default_limit
	return limit


def get_engine():
	# type: () -> sqlalchemy.Engine
	ucr = ConfigRegistry()
	ucr.load()

	password = open('/etc/admin-diary.secret').read().strip()

	dbms = ucr.get('admin/diary/dbms')
	dbhost = ucr.get('admin/diary/dbhost')
	if not dbhost:
		admin_diary_backend = ucr.get('admin/diary/backend') or 'localhost'
		dbhost = admin_diary_backend.split()[0]
	if dbhost == ucr.get('hostname') or dbhost == '%s.%s' % (ucr.get('hostname'), ucr.get('domainname')):
		dbhost = 'localhost'
	db_url = '%s://admindiary:%s@%s/admindiary' % (dbms, password, dbhost)
	if dbms == 'mysql':
		db_url = db_url + '?charset=utf8mb4'
	return sqlalchemy.create_engine(db_url, poolclass=NullPool)


def windowed_query(q, column, windowsize, single_entity=True):
	"""
	Break a Query into chunks on a given unique column (usually primary key), then fetch chunks using LIMIT only,
	adding a WHERE clause that will ensure we only fetch rows greater than the last one we fetched. This will work for
	basically any database backend. The potential downside is that the database needs to sort the full set of remaining
	rows for each chunk, which may be inefficient, even if the sort column is indexed. However, the approach is very
	simple and can likely work for most ordinary use cases for a primary key column on a database that does not support
	window functions.
	"""

	# TODO: single_entity is implemented in SqlAlchemy 1.3.11 and above.
	# After updating SqlAlchemy, single_entity should be removed from
	# function arguments, and resolved locally, as in line below:
	# single_entity = q.is_single_entity
	q = q.add_column(column).order_by(column)
	last_id = None

	while True:
		subq = q
		if last_id is not None:
			subq = subq.filter(column > last_id)
		chunk = subq.limit(windowsize).all()
		if not chunk:
			break
		last_id = chunk[-1][-1]
		for row in chunk:
			if single_entity:
				yield row[0]
			else:
				yield row[0:-1]


@contextmanager
def get_session(auto_commit=True):
	# type: (bool) -> Iterator[sqlalchemy.Session]
	session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=get_engine()))
	yield session
	if auto_commit:
		session.commit()
	session.remove()
	session.bind.dispose()


Base = declarative_base()


class Meta(Base):
	__tablename__ = 'meta'

	id = Column(Integer, Sequence('meta_id_seq'), primary_key=True)
	schema = Column(Integer, nullable=False)


entry_tags = Table(
	'entry_tags', Base.metadata,
	Column('entry_id', ForeignKey('entries.id'), primary_key=True),
	Column('tag_id', ForeignKey('tags.id'), primary_key=True)
)


class Event(Base):
	__tablename__ = 'events'

	id = Column(Integer, Sequence('event_id_seq'), primary_key=True)
	name = Column(String(190), nullable=False, unique=True, index=True)


class EventMessage(Base):
	__tablename__ = 'event_messages'

	event_id = Column(None, ForeignKey('events.id', ondelete='CASCADE'), primary_key=True)
	locale = Column(String(190), nullable=False, primary_key=True)
	message = Column(Text, nullable=False)
	locked = Column(Boolean)


class Entry(Base):
	__tablename__ = 'entries'

	id = Column(Integer, Sequence('entry_id_seq'), primary_key=True)
	username = Column(String(190), nullable=False, index=True)
	hostname = Column(String(190), nullable=False, index=True)
	message = Column(Text)
	timestamp = Column(DateTime(timezone=True), index=True)
	context_id = Column(String(190), index=True)
	event_id = Column(None, ForeignKey('events.id', ondelete='RESTRICT'), nullable=True)
	main_id = Column(None, ForeignKey('entries.id', ondelete='CASCADE'), nullable=True)

	event = relationship('Event')
	args = relationship('Arg', back_populates='entry')
	tags = relationship('Tag', secondary=entry_tags, back_populates='entries')
	comments = relationship('Entry', primaryjoin=context_id == context_id, foreign_keys=context_id, remote_side=context_id)


class Tag(Base):
	__tablename__ = 'tags'

	id = Column(Integer, Sequence('tag_id_seq'), primary_key=True)
	name = Column(String(190), nullable=False, unique=True, index=True)

	entries = relationship('Entry', secondary=entry_tags, back_populates='tags')


class Arg(Base):
	__tablename__ = 'args'

	id = Column(Integer, Sequence('arg_id_seq'), primary_key=True)
	entry_id = Column(None, ForeignKey('entries.id', ondelete='CASCADE'), index=True)
	key = Column(String(190), nullable=False, index=True)
	value = Column(String(190), nullable=False, index=True)

	entry = relationship('Entry')


class Client(object):
	def __init__(self, version, session):
		# type: (int, sqlalchemy.Session) -> None
		self.version = version
		self._session = session
		self._translation_cache = {}  # type: Dict[Tuple[str, str], str]

	def translate(self, event_name, locale):
		# type: (str, str) -> str
		key = (event_name, locale)
		if key not in self._translation_cache:
			event_message = self._session.query(EventMessage).filter(EventMessage.event_id == Event.id, EventMessage.locale == locale, Event.name == event_name).one_or_none()
			if event_message:
				translation = event_message.message
			else:
				translation = None
			self._translation_cache[key] = translation
		else:
			translation = self._translation_cache[key]
		return translation

	def options(self):
		# type: () -> dict
		ret = {}
		ret['tags'] = sorted([tag.name for tag in self._session.query(Tag).all()])
		ret['usernames'] = sorted([username[0] for username in self._session.query(Entry.username).distinct()])
		ret['hostnames'] = sorted([hostname[0] for hostname in self._session.query(Entry.hostname).distinct()])
		ret['events'] = sorted([event.name for event in self._session.query(Event).all()])
		return ret

	def add_tag(self, name):
		# type: (str) -> Tag
		obj = self._session.query(Tag).filter(Tag.name == name).one_or_none()
		if obj is None:
			obj = Tag(name=name)
			self._session.add(obj)
			self._session.flush()
		return obj

	def add_event(self, name):
		# type: (str) -> Event
		obj = self._session.query(Event).filter(Event.name == name).one_or_none()
		if obj is None:
			obj = Event(name=name)
			self._session.add(obj)
			self._session.flush()
		return obj

	def add_event_message(self, event_id, locale, message, force):
		# type: (int, str, str, bool) -> bool
		event_message_query = self._session.query(EventMessage).filter(EventMessage.locale == locale, EventMessage.event_id == event_id)
		event_message = event_message_query.one_or_none()
		if event_message is None:
			event_message = EventMessage(event_id=event_id, locale=locale, message=message, locked=force)
			self._session.add(event_message)
			self._session.flush()
			return True
		else:
			if force:
				event_message_query.update({'locked': True, 'message': message})
				self._session.flush()
				return True
		return False

	def add(self, diary_entry):
		# type: (DiaryEntry) -> None
		if diary_entry.event_name == 'COMMENT':
			entry_message = diary_entry.message.get('en')
			event_id = None
		else:
			get_logger().debug('Searching for Event %s' % diary_entry.event_name)
			entry_message = None
			event = self.add_event(diary_entry.event_name)
			event_id = event.id
			get_logger().debug('Found Event ID %s' % event.id)
			if diary_entry.message:
				for locale, message in diary_entry.message.items():
					get_logger().debug('Trying to insert message for %s' % locale)
					if self.add_event_message(event.id, locale, message, False):
						get_logger().debug('Found no existing one. Inserted %r' % message)
			else:
				get_logger().debug('No further message given, though')
		entry = Entry(username=diary_entry.username, hostname=diary_entry.hostname, timestamp=diary_entry.timestamp, context_id=diary_entry.context_id, event_id=event_id, message=entry_message)
		self._session.add(entry)
		main_id = self._session.query(func.min(Entry.id)).filter(Entry.context_id == entry.context_id).scalar()
		if main_id:
			entry.main_id = main_id
		for tag in diary_entry.tags:
			tag = self.add_tag(tag)
			entry.tags.append(tag)
		for key, value in diary_entry.args.items():
			entry.args.append(Arg(key=key, value=value))
		get_logger().info('Successfully added %s (%s)' % (diary_entry.context_id, diary_entry.event_name))

	def query(self, time_from=None, time_until=None, tag=None, event=None, username=None, hostname=None, message=None, locale='en'):
		limit = get_query_limit()

		with get_session(False) as session:
			return self.__query(session, limit, time_from, time_until, tag, event, username, hostname, message, locale)

	def __query(self, session, limit, time_from, time_until, tag, event, username, hostname, message, locale):
		query = session.query(Entry).\
			outerjoin(Event, Event.id == Entry.event_id).\
			outerjoin(Arg, Arg.entry_id == Entry.id).\
			options(joinedload(Entry.event)).\
			options(joinedload(Entry.args)).\
			options(joinedload(Entry.comments)).\
			order_by(Entry.id)

		if time_from:
			query = query.filter(Entry.timestamp >= time_from)
		if time_until:
			query = query.filter(Entry.timestamp < time_until)
		if tag:
			query = query.filter(Entry.tags.any(Tag.name == tag))
		if event:
			query = query.filter(Entry.event.has(name=event))
		if username:
			query = query.filter(Entry.username == username)
		if hostname:
			query = query.filter(Entry.hostname == hostname)
		if message:
			# in case message is given, we search in entries, event_messages and args tables
			query = query.outerjoin(EventMessage, EventMessage.event_id == Entry.event_id)

			# form filters array
			filters = []
			for pat in message.split():
				filters.append(
					or_(
						Entry.message.ilike('%{}%'.format(pat)),
						and_(
							EventMessage.locale == locale,
							EventMessage.message.ilike('%{}%'.format(pat))
						),
						Entry.args.any(Arg.value == pat),
					)
				)

			# find all entries matching given message criterion
			query = query.filter(or_(*filters))

		res = []
		for entry in windowed_query(query, Entry.id, limit):
			if len(res) >= limit:
				break

			event = entry.event
			if event:
				event_name = event.name
			else:
				event_name = 'COMMENT'
			args = dict((arg.key, arg.value) for arg in entry.args)
			comments = sum(1 for e in entry.comments if e.message and e.context_id == entry.context_id)
			res.append({
				'id': entry.id,
				'date': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
				'event_name': event_name,
				'hostname': entry.hostname,
				'username': entry.username,
				'context_id': entry.context_id,
				'message': entry.message,
				'args': args,
				'comments': comments > 0,
			})

		return res[:limit]

	def get(self, context_id):
		# type: (int) -> List[Dict[str, Any]]
		res = []
		query = self._session.query(Entry).\
			outerjoin(Event, Event.id == Entry.event_id).\
			outerjoin(Arg, Arg.entry_id == Entry.id).\
			options(joinedload(Entry.event)).\
			options(joinedload(Entry.args)).\
			filter(Entry.context_id == context_id).\
			order_by(Entry.id)

		for entry in query.all():
			args = dict((arg.key, arg.value) for arg in entry.args)
			tags = [tag.name for tag in entry.tags]
			event = entry.event
			if event:
				event_name = event.name
			else:
				event_name = 'COMMENT'
			obj = {
				'id': entry.id,
				'username': entry.username,
				'hostname': entry.hostname,
				'message': entry.message,
				'args': args,
				'date': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
				'tags': tags,
				'context_id': entry.context_id,
				'event_name': event_name,
			}
			res.append(obj)
		return res


@contextmanager
def get_client(version):
	# type: (int) -> Iterator[Client]
	if version != 1:
		raise UnsupportedVersion(version)
	with get_session() as session:
		client = Client(version=version, session=session)
		yield client


class UnsupportedVersion(Exception):
	def __str__(self):
		return 'Version %s of the Admin Diary Backend is not supported' % (self.args[0])
