#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2019 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

from contextlib import contextmanager
from functools import partial

import sqlalchemy
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Sequence, Text, DateTime, func, Table

from univention.config_registry import ConfigRegistry

from univention.admindiary import get_logger

ucr = ConfigRegistry()
ucr.load()

password = open('/etc/admin-diary.secret').read().strip()

dbms = ucr.get('admin/diary/dbms')
dbhost = ucr.get('admin/diary/dbhost', 'localhost')

get_logger = partial(get_logger, 'backend')

db_url = '%s://admindiary:%s@%s/admindiary' % (dbms, password, dbhost)
engine = sqlalchemy.create_engine(db_url, echo=True)
Session = sessionmaker(bind=engine)

@contextmanager
def get_session():
	session = Session()
	yield session
	session.commit()
	session.close()




Base = declarative_base()

entry_args = Table('entry_args', Base.metadata,
    Column('entry_id', ForeignKey('entries.id'), primary_key=True),
    Column('arg_id', ForeignKey('args.id'), primary_key=True)
)
entry_tags = Table('entry_tags', Base.metadata,
    Column('entry_id', ForeignKey('entries.id'), primary_key=True),
    Column('tag_id', ForeignKey('tags.id'), primary_key=True)
)

class Event(Base):
	__tablename__ = 'events'

	id = Column(Integer, Sequence('event_id_seq'), primary_key=True)
	name = Column(String(255), nullable=False, unique=True, index=True)

class EventMessage(Base):
	__tablename__ = 'event_messages'

	event_id = Column(None, ForeignKey('events.id', ondelete='CASCADE'), primary_key=True)
	locale = Column(String(255), nullable=False, primary_key=True)
	message = Column(Text, nullable=False)
	locked = Column(Boolean)

class Entry(Base):
	__tablename__ = 'entries'

	id = Column(Integer, Sequence('entry_id_seq'), primary_key=True)
	username = Column(String(255), nullable=False, index=True)
	hostname = Column(String(255), nullable=False, index=True)
	message = Column(Text)
	timestamp = Column(DateTime(timezone=True), index=True)
	context_id = Column(String(255), index=True)
	event_id = Column(None, ForeignKey('events.id', ondelete='RESTRICT'), nullable=True)
	main_id = Column(None, ForeignKey('entries.id', ondelete='CASCADE'), nullable=True)

	event = relationship('Event')
	tags = relationship('Tag',
                        secondary=entry_tags,
                        back_populates='entries'
                        )
	args = relationship('Arg',
                        secondary=entry_args,
                        back_populates='entries'
                        )

class Tag(Base):
	__tablename__ = 'tags'

	id = Column(Integer, Sequence('tag_id_seq'), primary_key=True)
	name = Column(String(255), nullable=False, unique=True, index=True)

	entries = relationship('Entry',
                        secondary=entry_tags,
                        back_populates='tags'
                        )

class Arg(Base):
	__tablename__ = 'args'

	id = Column(Integer, Sequence('arg_id_seq'), primary_key=True)
	value = Column(String(255), nullable=False, unique=True, index=True)

	entries = relationship('Entry',
                        secondary=entry_args,
                        back_populates='args'
                        )

def translate(event_name, locale, session):
	key = (event_name, locale)
	if key not in translate._cache:
		event_message = session.query(EventMessage).filter(EventMessage.event_id == Event.id, EventMessage.locale == locale, Event.name == event_name).one_or_none()
		if event_message:
			translation = event_message.message
		else:
			translation = None
		translate._cache[key] = translation
	else:
		translation = translate._cache[key]
	return translation
translate._cache = {}

def options(session):
	ret = {}
	ret['tags'] = [tag.name for tag in session.query(Tag).all()]
	ret['usernames'] = [username[0] for username in session.query(Entry.username).distinct()]
	ret['hostnames'] = [hostname[0] for hostname in session.query(Entry.hostname).distinct()]
	ret['events'] = [event.name for event in session.query(Event).all()]
	return ret

def add_arg(value, session):
	obj = session.query(Arg).filter(Arg.value == value).one_or_none()
	if obj is None:
		obj = Arg(value=value)
		session.add(obj)
		session.flush()
	return obj

def add_tag(name, session):
	obj = session.query(Tag).filter(Tag.name == name).one_or_none()
	if obj is None:
		obj = Tag(name=name)
		session.add(obj)
		session.flush()
	return obj

def add_event(name, session):
	obj = session.query(Event).filter(Event.name == name).one_or_none()
	if obj is None:
		obj = Event(name=name)
		session.add(obj)
		session.flush()
	return obj

def add_event_message(event_id, locale, message, force, session):
	event_message_query = session.query(EventMessage).filter(EventMessage.locale == locale, EventMessage.event_id == event_id)
	event_message = event_message_query.one_or_none()
	if event_message is None:
		event_message = EventMessage(event_id=event_id, locale=locale, message=message, locked=force)
		session.add(event_message)
		session.flush()
		return True
	else:
		if force:
			event_message_query.update({'locked': True, 'message': message})
			session.flush()
			return True
	return False

def add(diary_entry, session):
	if diary_entry.event_name == 'COMMENT':
		entry_message = diary_entry.message.get('en')
		event_id = None
	else:
		get_logger().debug('Searching for Event %s' % diary_entry.event_name)
		entry_message = None
		event = add_event(diary_entry.event_name, session)
		event_id = event.id
		get_logger().debug('Found Event ID %s' % event.id)
		if diary_entry.message:
			for locale, message in diary_entry.message.iteritems():
				get_logger().debug('Trying to insert message for %s' % locale)
				if add_event_message(event.id, locale, message, False, session):
					get_logger().debug('Found no existing one. Inserted %r' % message)
		else:
			get_logger().debug('No further message given, though')
	entry = Entry(username=diary_entry.username, hostname=diary_entry.hostname, timestamp=diary_entry.timestamp, context_id=diary_entry.context_id, event_id=event_id, message=entry_message)
	session.add(entry)
	main_id = session.query(func.min(Entry.id)).filter(Entry.context_id == entry.context_id).scalar()
	if main_id:
		entry.main_id = main_id
	session.flush()
	for tag in diary_entry.tags:
		tag = add_tag(tag, session)
		entry.tags.append(tag)
	for arg in diary_entry.args:
		arg = add_arg(arg, session)
		entry.args.append(arg)
	get_logger().info('Successfully added %s to %s. (%s)' % (diary_entry.context_id, engine.url.drivername, diary_entry.event_name))

def _one_query(ids, result):
	if ids is not None and not ids:
		return set()
	new_ids = set()
	for entry in result:
		new_ids.add(entry.main_id)
	if ids is None:
		return new_ids
	else:
		return ids.intersection(new_ids)

def query(session, time_from=None, time_until=None, tag=None, event=None, username=None, hostname=None, message=None, locale='en'):
	ids = None
	if time_from:
		ids = _one_query(ids, session.query(Entry).filter(Entry.timestamp >= time_from))
	if time_until:
		ids = _one_query(ids, session.query(Entry).filter(Entry.timestamp < time_until))
	if tag:
		ids = _one_query(ids, session.query(Entry).filter(Entry.tags.any(Tag.name == tag)))
	if event:
		ids = _one_query(ids, session.query(Entry).filter(Entry.event.has(name=event)))
	if username:
		ids = _one_query(ids, session.query(Entry).filter(Entry.username == username))
	if hostname:
		ids = _one_query(ids, session.query(Entry).filter(Entry.hostname == hostname))
	if message:
		pattern_ids = set()
		for pat in message.split():
			pattern_ids.update(_one_query(None, session.query(Entry).filter(Entry.message.ilike('%{}%'.format(pat)))))
			pattern_ids.update(_one_query(None, session.query(Entry).join(EventMessage, Entry.event_id == EventMessage.event_id).filter(Entry.event_id == EventMessage.event_id, EventMessage.locale == locale, EventMessage.message.ilike('%{}%'.format(pat)))))
			pattern_ids.update(_one_query(None, session.query(Entry).filter(Entry.args.any(Arg.value == pat))))
		if ids is None:
			ids = pattern_ids
		else:
			ids.intersection_update(pattern_ids)
	if ids is None:
		entries = session.query(Entry).filter(Entry.main_id == Entry.id)
	else:
		entries = session.query(Entry).filter(Entry.id.in_(ids))
	res = []
	for entry in entries:
		event = entry.event
		if event:
			event_name = event.name
		else:
			event_name = 'COMMENT'
		args = [arg.value for arg in entry.args]
		group = session.query(Entry).filter(Entry.context_id == entry.context_id).count()
		res.append({
			'id': entry.id,
			'date': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
			'event_name': event_name,
			'hostname': entry.hostname,
			'username': entry.username,
			'context_id': entry.context_id,
			'message': entry.message,
			'args': args,
			'amendments': group > 1,
		})
	return res

def get(context_id, session):
	res = []
	for entry in session.query(Entry).filter(Entry.context_id == context_id):
		args = [arg.value for arg in entry.args]
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
