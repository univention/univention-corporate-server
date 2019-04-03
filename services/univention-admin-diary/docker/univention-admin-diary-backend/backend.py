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

import json
import typing
import logging
from contextlib import contextmanager
from socket import gethostname
from datetime import datetime

import sqlalchemy
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Sequence, Text, DateTime, func, Table

from flask import Blueprint, Flask
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from flask_restplus import Api, Resource, abort, fields, reqparse
from flask_restplus.inputs import datetime_from_iso8601
from werkzeug.contrib.fixers import ProxyFix


logging.getLogger().setLevel(logging.DEBUG)  # INFO


authorizations = {
	'basic': {'type': 'basic'}
}  # https://swagger.io/docs/specification/2-0/authentication/
auth = HTTPBasicAuth()

API_VERSION = 2
ALLOWED_TYPES = ('Entry v1',)
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.wsgi_app = ProxyFix(app.wsgi_app)
blueprint = Blueprint('api', __name__, url_prefix='/admindiary/api/v{}'.format(API_VERSION))
api = Api(
	blueprint,
	version=API_VERSION,
	title='Univention Admin Diary API',
	description='API to create entries in the Admin Diary.',
	authorizations=authorizations,
	security='basic',
)
app.register_blueprint(blueprint)
db = SQLAlchemy(app)


def get_engine_url():
	# ucr = ConfigRegistry()
	# ucr.load()
	#
	# password = open('/etc/admin-diary.secret').read().strip()
	#
	# dbms = ucr.get('admin/diary/dbms')
	# dbhost = ucr.get('admin/diary/dbhost')
	# if not dbhost:
	# 	admin_diary_backend = ucr.get('admin/diary/backend') or 'localhost'
	# 	dbhost = admin_diary_backend.split()[0]
	# if dbhost == ucr.get('hostname') or dbhost == '%s.%s' % (ucr.get('hostname'), ucr.get('domainname')):
	# 	dbhost = 'localhost'
	dbms = 'mysql'
	password = 'mnultnm8KkUy6nZgQmEi'
	dbhost = '10.200.3.141'
	db_url = '%s://admindiary:%s@%s/admindiary' % (dbms, password, dbhost)
	if dbms == 'mysql':
		db_url = db_url + '?charset=utf8mb4'
	return db_url


db_url = get_engine_url()
app.config['SQLALCHEMY_DATABASE_URI'] = db_url


def get_engine():
	return sqlalchemy.create_engine(db_url)


db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=get_engine()))


# def make_session_class():
# 	if make_session_class._session is None:
# 		engine = get_engine()
# 		make_session_class._session = sessionmaker(bind=engine)
# 	return make_session_class._session
# make_session_class._session = None
#
#
# @contextmanager
# def get_session():
# 	session = make_session_class()()
# 	yield session
# 	session.commit()
# 	session.close()


@app.teardown_appcontext
def shutdown_session(exception=None):
	db_session.remove()


Base = declarative_base()


class Meta(Base):
	__tablename__ = 'meta'

	id = Column(Integer, Sequence('meta_id_seq'), primary_key=True)
	schema = Column(Integer, nullable=False)


entry_tags = Table('entry_tags', Base.metadata,
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
	tags = relationship('Tag',
						secondary=entry_tags,
						back_populates='entries'
						)


class Tag(Base):
	__tablename__ = 'tags'

	id = Column(Integer, Sequence('tag_id_seq'), primary_key=True)
	name = Column(String(190), nullable=False, unique=True, index=True)

	entries = relationship('Entry',
						secondary=entry_tags,
						back_populates='tags'
						)


class Arg(Base):
	__tablename__ = 'args'

	id = Column(Integer, Sequence('arg_id_seq'), primary_key=True)
	entry_id = Column(None, ForeignKey('entries.id', ondelete='CASCADE'), index=True)
	key = Column(String(190), nullable=False, index=True)
	value = Column(String(190), nullable=False, index=True)

	entry = relationship('Entry')


class Client(object):
	def __init__(self, version, session):
		self.version = version
		self._session = session
		self._translation_cache = {}

	def translate(self, event_name, locale):
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
		ret = {}
		ret['tags'] = sorted([tag.name for tag in self._session.query(Tag).all()])
		ret['usernames'] = sorted([username[0] for username in self._session.query(Entry.username).distinct()])
		ret['hostnames'] = sorted([hostname[0] for hostname in self._session.query(Entry.hostname).distinct()])
		ret['events'] = sorted([event.name for event in self._session.query(Event).all()])
		return ret

	def add_tag(self, name):
		obj = self._session.query(Tag).filter(Tag.name == name).one_or_none()
		if obj is None:
			obj = Tag(name=name)
			self._session.add(obj)
			self._session.flush()
		return obj

	def add_event(self, name):
		obj = self._session.query(Event).filter(Event.name == name).one_or_none()
		if obj is None:
			obj = Event(name=name)
			self._session.add(obj)
			self._session.flush()
		return obj

	def add_event_message(self, event_id, locale, message, force):
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
		if diary_entry.event_name == 'COMMENT':
			entry_message = diary_entry.message.get('en')
			event_id = None
		else:
			app.logger.debug('Searching for Event %s' % diary_entry.event_name)
			entry_message = None
			event = self.add_event(diary_entry.event_name)
			event_id = event.id
			app.logger.debug('Found Event ID %s' % event.id)
			if diary_entry.message:
				for locale, message in diary_entry.message.items():
					app.logger.debug('Trying to insert message for %s' % locale)
					if self.add_event_message(event.id, locale, message, False):
						app.logger.debug('Found no existing one. Inserted %r' % message)
			else:
				app.logger.debug('No further message given, though')
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
		app.logger.info('Successfully added %s (%s)' % (diary_entry.context_id, diary_entry.event_name))

	def _one_query(self, ids, result):
		if ids is not None and not ids:
			return set()
		new_ids = set()
		for entry in result:
			new_ids.add(entry.id)
		if ids is None:
			return new_ids
		else:
			return ids.intersection(new_ids)

	def query(self, time_from=None, time_until=None, tag=None, event=None, username=None, hostname=None, message=None, locale='en'):
		ids = None
		if time_from:
			ids = self._one_query(ids, self._session.query(Entry).filter(Entry.timestamp >= time_from))
		if time_until:
			ids = self._one_query(ids, self._session.query(Entry).filter(Entry.timestamp < time_until))
		if tag:
			ids = self._one_query(ids, self._session.query(Entry).filter(Entry.tags.any(Tag.name == tag)))
		if event:
			ids = self._one_query(ids, self._session.query(Entry).filter(Entry.event.has(name=event)))
		if username:
			ids = self._one_query(ids, self._session.query(Entry).filter(Entry.username == username))
		if hostname:
			ids = self._one_query(ids, self._session.query(Entry).filter(Entry.hostname == hostname))
		if message:
			pattern_ids = set()
			for pat in message.split():
				pattern_ids.update(self._one_query(None, self._session.query(Entry).filter(Entry.message.ilike('%{}%'.format(pat)))))
				pattern_ids.update(self._one_query(None, self._session.query(Entry).join(EventMessage, Entry.event_id == EventMessage.event_id).filter(Entry.event_id == EventMessage.event_id, EventMessage.locale == locale, EventMessage.message.ilike('%{}%'.format(pat)))))
				pattern_ids.update(self._one_query(None, self._session.query(Entry).filter(Entry.args.any(Arg.value == pat))))
			if ids is None:
				ids = pattern_ids
			else:
				ids.intersection_update(pattern_ids)
		if ids is None:
			entries = self._session.query(Entry).filter(Entry.event_id != None)
		else:
			entries = self._session.query(Entry).filter(Entry.id.in_(ids), Entry.event_id != None)
		res = []
		for entry in entries:
			event = entry.event
			if event:
				event_name = event.name
			else:
				event_name = 'COMMENT'
			args = dict((arg.key, arg.value) for arg in entry.args)
			comments = self._session.query(Entry).filter(Entry.context_id == entry.context_id, Entry.message != None).count()
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
		return res

	def get(self, context_id):
		res = []
		for entry in self._session.query(Entry).filter(Entry.context_id == context_id).order_by('id'):
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
	if version != 1:
		raise UnsupportedVersion(version)
	# with get_session() as session:
	# 	client = Client(version=version, session=session)
	# 	yield client
	yield Client(version=version, session=db_session)


class UnsupportedVersion(Exception):
	def __str__(self):
		return 'Version %s of the Admin Diary Backend is not supported' % (self.args[0])


class DiaryEntry(object):
	def __init__(self, username, message, args, tags, context_id, event_name, hostname=None, timestamp=None):
		self.username = username
		self.hostname = hostname or gethostname()
		self.message = message
		self.args = args
		self.timestamp = timestamp or datetime.now()
		self.tags = tags
		self.context_id = context_id
		self.event_name = event_name

	def assert_types(self):  # type: () -> None
		if not isinstance(self.username, str):
			raise TypeError('Username has to be "string"')
		if not isinstance(self.hostname, str):
			raise TypeError('Hostname has to be "string"')
		if not isinstance(self.args, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in self.args.items()):
			raise TypeError('Args have to be "dict of string/string"')
		if self.message is not None:
			if not isinstance(self.message, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in self.message.items()):
				raise TypeError('Message has to be "dict of string/string"')
			for locale, message in self.message.items():
				try:
					message.format(**self.args)
				except:
					raise TypeError('Message (%s, %r) has wrong format for given args (%r).', locale, message, self.args)
		if not isinstance(self.timestamp, datetime):
			raise TypeError('timestamp has to be "datetime"')
		if not isinstance(self.tags, list) or not all(isinstance(tag, str) for tag in self.tags):
			raise TypeError('Tags have to be "list of string"')
		if not isinstance(self.context_id, str):
			raise TypeError('Diary ID has to be "string"')
		if not isinstance(self.event_name, str):
			raise TypeError('Event name has to be "string"')

	def to_json(self):  # type: () -> str
		attrs = {
			'username': self.username,
			'hostname': self.hostname,
			'message': self.message,
			'args': self.args,
			'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S%z'),
			'tags': self.tags,
			'context_id': self.context_id,
			'event': self.event_name,
			'type': 'Entry v1',
			}
		return json.dumps(attrs)

	@classmethod
	def from_json(cls, body):  # type: (str) -> DiaryEntry
		json_body = json.loads(body)
		entry = cls(json_body['username'], json_body['message'], json_body['args'], json_body['tags'], json_body['context_id'], json_body['event'])
		entry.timestamp = datetime.strptime(json_body['timestamp'], '%Y-%m-%d %H:%M:%S')
		entry.hostname = json_body['hostname']
		entry.assert_types()
		return entry


def process(values):  # type: (typing.Dict[str, typing.Any]) -> None
	json_string = json.dumps(values)
	if values.get('type') == 'Entry v1':
		entry = DiaryEntry.from_json(json_string)
		add_entry_v1(entry)
	else:
		app.logger.error('Unsupported values: %r' % values)


def get_events_to_reject():  # type: () -> typing.List[str]
	ucrv = 'admin/diary/reject'
	blocked_events = ''  # ucr.get(ucrv)
	if blocked_events:
		return blocked_events.split()
	return []


def add_entry_v1(entry):  # type: (DiaryEntry) -> None
	blocked_events = get_events_to_reject()
	if entry.event_name in blocked_events:
		app.logger.info('Rejecting %s' % entry.event_name)
		return
	with get_client(version=1) as client:
		client.add(entry)


@auth.verify_password
def verify_pw(username, password):  # type: (str, str) -> bool
	app.logger.debug('*** username=%r password=%r', username, password)
	if not (username and password):
		return False
	try:
		# TODO: try LDAP bind
		return True
	except:  # TODO: except LDAP.error
		return False


create_entry_parser = reqparse.RequestParser()
create_entry_parser.add_argument('username', type=str, required=True, help='TODO.')
create_entry_parser.add_argument('hostname', type=str, required=True, help='TODO.')
create_entry_parser.add_argument('message', type=dict, required=True, help='TODO.')
create_entry_parser.add_argument('args', type=dict, default={}, help='TODO.')
create_entry_parser.add_argument('timestamp', type=datetime_from_iso8601, required=True, help='TODO.')
create_entry_parser.add_argument('tags', type=str, default=[], action='append', help='TODO.')
create_entry_parser.add_argument('context_id', type=str, required=True, help='TODO.')
create_entry_parser.add_argument('event', type=str, required=True, help='TODO.')
create_entry_parser.add_argument('type', type=str, required=True, help='API version (must be "Entry v1").')


entry_model = api.model('Model', {
	'username': fields.String,
	'hostname': fields.String,
	'message': fields.Raw,
	'args': fields.Raw,
	'timestamp': fields.DateTime(dt_format='iso8601'),
	'tags': fields.List(fields.String),
	'context_id': fields.String,
	'event': fields.String,
	'type': fields.String,
})


@api.route('/')
@api.doc('AdminDiaryEntry')
class AdminDiaryEntryList(Resource):
	method_decorators = (auth.login_required,)

	@api.doc('create')
	@api.expect(entry_model)
	@api.marshal_with(entry_model, skip_none=True, code=201)
	@api.expect(create_entry_parser)
	def post(self):  # type: () -> typing.Tuple[typing.Dict[str, typing.Any], int]
		"""Create a new AdminDiaryEntry object."""
		app.logger.debug('AdminDiaryEntryList.post()')
		args = create_entry_parser.parse_args()
		app.logger.debug('AdminDiaryEntryList.post() args=%r', args)
		if args['type'] not in ALLOWED_TYPES:
			msg = '"type" {!r} not allowed.'.format(args['type'])
			app.logger.error('400: %s', msg)
			abort(400, msg)
		del args['type']
		args['event_name'] = args.pop('event')
		add_entry_v1(DiaryEntry(**args))
		return {}, 201


if __name__ == '__main__':
	app.run(debug=True)
