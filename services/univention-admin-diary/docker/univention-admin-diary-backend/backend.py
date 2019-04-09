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

import os
import json
import typing
import hashlib
import logging
import datetime
from contextlib import contextmanager
from socket import gethostname
from datetime import datetime

import sqlalchemy
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Sequence, Text, DateTime, func, Table

from flask import Blueprint, Flask, request, g
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from flask_restplus import Api, Resource, abort, fields, reqparse
from flask_restplus.inputs import datetime_from_iso8601
from werkzeug.contrib.fixers import ProxyFix

from ldap3 import Server, Connection, ALL, BASE
from ldap3.core.exceptions import LDAPException, LDAPInvalidCredentialsResult

from pymemcache.client.base import Client as MemcachedClient

DEBUG = os.environ.get('DEBUG') == 'TRUE'

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

# TODO: get from env and disk when started by appcenter
LDAP_HOST = '10.200.3.141'
LDAP_PORT = 7636
LDAP_BASE_DN = 'dc=uni,dc=dtr'
LDAP_HOSTDN = f'cn=m141-ox,cn=dc,cn=computers,{LDAP_BASE_DN}'
LDAP_HOST_PW = 'n6VgQ7fKr3n5jJIbxebn'
ADMIN_DIARY_WRITER_GROUP_DN = f'cn=admin-diary-writers,cn=groups,{LDAP_BASE_DN}'
MEMCACHED_HOST = 'memcached'
MEMBER_CACHE_EXPIRE_SECONDS = 60
AUTH_CACHE_EXPIRE_SECONDS = 60


def get_engine_url():  # type: () -> str
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
	return os.environ.get('DB_URI', 'mysql://admindiary:mnultnm8KkUy6nZgQmEi@10.200.3.141/admindiary?charset=utf8mb4')


db_url = get_engine_url()
app.config['SQLALCHEMY_DATABASE_URI'] = db_url


def get_engine():
	return sqlalchemy.create_engine(db_url, echo=DEBUG)


db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=get_engine()))


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
		app.logger.debug(repr(ids))
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
				'timestamp': entry.timestamp,
				'username': entry.username,
				'hostname': entry.hostname,
				'message': entry.message,
				'args': args,
				'context_id': entry.context_id,
				'event': event_name,
				'comments': comments > 0,
			})
		return res

	def get(self, context_id):  # type: (str) -> typing.List[typing.Dict[str, typing.Any]]
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
def get_client(version):  # type: (int) -> Client
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


class Cache(object):
	def __init__(self, object_type, timeout):  # type: (str, int) -> None
		self._object_type = object_type
		self.timeout = timeout
		self._memcache_kwargs = {
			'server': (MEMCACHED_HOST, 11211),
			'serializer': self._json_serializer,
			'deserializer': self._json_deserializer,
			'connect_timeout': 1.0,
			'timeout': 1.0,
			'no_delay': True,
			'ignore_exc': False,
		}


	@property
	def _memcached_client(self):  # type: () -> MemcachedClient
		try:
			client = g.get('memcached_client')
		except RuntimeError as exc:
			# Working outside of flask application context (from interactive console).
			# Don't store in flask.g
			app.logger.warning('Ignoring RuntimeError: %s', str(exc).split('\n', 1)[0])
			return MemcachedClient(**self._memcache_kwargs)
		if client is None:
			g.memcached_client = MemcachedClient(**self._memcache_kwargs)
		return g.memcached_client

	def _memcached_key(self, key):  # type: (str) -> str
		return f'{self._object_type}_{key}'

	@staticmethod
	def _json_serializer(key, value):
		if isinstance(value, str):
			return value, 1
		if isinstance(value, set):
			value = list(value)
		return json.dumps(value), 2

	@staticmethod
	def _json_deserializer(key, value, flags):
		if flags == 1:
			return value.decode('utf-8')
		elif flags == 2:
			res = json.loads(value.decode('utf-8'))
			if isinstance(res, list):
				res = set(res)
			return res
		raise ValueError("Unknown serialization format")

	def __contains__(self, item):  # type: (str) -> bool
		res = self._memcached_client.get(self._memcached_key(item))
		return res is not None

	def get(self, key, default=None):
		return self._memcached_client.get(self._memcached_key(key), default)

	def save(self, key, value, expire=None):
		expire = expire or self.timeout
		return self._memcached_client.add(self._memcached_key(key), value, expire)


class AdminDiaryAuth(object):
	group_cache = Cache('members', MEMBER_CACHE_EXPIRE_SECONDS)
	auth_cache = Cache('auth', AUTH_CACHE_EXPIRE_SECONDS)

	def __init__(
			self,
			ldap_host_address,  # type: str
			ldap_host_port,  # type: int
			ldap_host_dn,  # type: str
			ldap_host_password  # type: str
	):
		# type: (...) -> None
		self.ldap_host_address = ldap_host_address
		self.ldap_host_port = ldap_host_port
		self.ldap_host_dn = ldap_host_dn
		self.ldap_host_password = ldap_host_password
		self._ldap_connection = None

	def ldap_connection(self, dn, password):  # type: (str, str) -> Connection
		"""context manager"""
		if not self._ldap_connection:
			server = Server(host=self.ldap_host_address, port=self.ldap_host_port, use_ssl=True, get_info='ALL')
			self._ldap_connection = Connection(
				server, user=dn, password=password, version=3, authentication='SIMPLE', client_strategy='SYNC',
				auto_referrals=True, check_names=True, read_only=False, lazy=False, raise_exceptions=True
			)
		return self._ldap_connection

	def machine_connection(self):  # type: () -> Connection
		"""context manager"""
		return self.ldap_connection(self.ldap_host_dn, self.ldap_host_password)

	def group_members(self, dn, known_groups=None):
		# type: (str, typing.Optional[typing.Iterable[str]]) -> typing.Iterable[str]
		known_groups = known_groups or set()
		users = set()
		groups = set()

		with self.machine_connection() as conn:
			try:
				if not conn.search(
						dn,
						'(objectClass=univentionGroup)',
						attributes=['uniqueMember'],
						search_scope=BASE
				):
					app.logger.error('Looking up group %r: %s', dn, conn.last_error)
					return []
			except LDAPException as exc:
				app.logger.exception('Looking up group %r: %s', dn, exc)
				return []
			members = conn.entries[0].uniqueMember
			for member in [m for m in members if m not in known_groups]:
				res = conn.search(member, '(objectClass=univentionGroup)', attributes=['uniqueMember'], search_scope=BASE)
				if res:
					groups.add(member)
				else:
					users.add(member)
			for group in groups:
				users.update(set(self.group_members(group, known_groups=set(known_groups).union(groups))))  # recursion

		return users

	def allowed_user_dns(self):  # type: () -> typing.Iterable[str]
		members = self.group_cache.get(ADMIN_DIARY_WRITER_GROUP_DN)
		if members is None:
			# group_cache miss
			members = self.group_members(ADMIN_DIARY_WRITER_GROUP_DN)
			self.group_cache.save(ADMIN_DIARY_WRITER_GROUP_DN, members)
		# else: group_cache hit
		else:
		return members

	def verify_pw(self, dn, password):  # type: (str, str) -> bool
		if not (dn and password):
			return False

		# 1. authentication
		cache_key = '{}/{}'.format(dn, hashlib.sha256(password.encode('utf-8')).hexdigest())
		authenticated = self.auth_cache.get(cache_key)
		if authenticated is None:
			try:
				with self.ldap_connection(dn, password) as conn:
					assert conn.bound is True
					app.logger.info('LDAP bind: sucessfully authenticated as %r to %r.', dn, LDAP_HOST)
					authenticated = True
			except LDAPInvalidCredentialsResult as exc:
				app.logger.info('LDAP bind: denied access as %r to %r: %s', dn, LDAP_HOST, exc)
				authenticated = False
			except LDAPException as exc:
				app.logger.error('LDAP bind: trying to bind as %r to %r: %s', dn, LDAP_HOST, exc)
				authenticated = False
			self.auth_cache.save(cache_key, authenticated)
		elif authenticated is True:
			app.logger.info('Cache: sucessfully authenticated as %r.', dn)
		else:
			app.logger.info('Cache: denied access to %r.', dn)
			authenticated = False

		# 2. authorization
		if not authenticated:
			return False
		elif authenticated and dn in self.allowed_user_dns():
			return True
		else:
			app.logger.info('User %r not authorized (not member of %r).', dn, ADMIN_DIARY_WRITER_GROUP_DN.split(',', 1)[0])
			return False


@auth.verify_password
def verify_pw(username, password):  # type: (str, str) -> bool
	if not g.get('auth'):
		g.auth = AdminDiaryAuth(LDAP_HOST, LDAP_PORT, LDAP_HOSTDN, LDAP_HOST_PW)
	res = g.auth.verify_pw(username, password)
	return res


create_entry_parser = reqparse.RequestParser()
create_entry_parser.add_argument('username', type=str, required=True, help='User that triggered the logged event.')
create_entry_parser.add_argument('hostname', type=str, required=True, help='Host on which the event took place.')
create_entry_parser.add_argument('message', type=dict, required=True, help='Message.')
create_entry_parser.add_argument('args', type=dict, default={}, help='Arguments to fill variables in message text.')
create_entry_parser.add_argument('timestamp', type=datetime_from_iso8601, required=True, help='Date and time event took place.')
create_entry_parser.add_argument('tags', type=str, default=[], action='append', help='Tags.')
create_entry_parser.add_argument('context_id', type=str, required=True, help='TODO.')
create_entry_parser.add_argument('event', type=str, required=True, help='Event ID.')
create_entry_parser.add_argument('type', type=str, required=True, help='API version (must be "Entry v1").')

query_entries_parser = reqparse.RequestParser()
query_entries_parser.add_argument('time_from', type=datetime_from_iso8601, required=False, help='TODO.')
query_entries_parser.add_argument('time_until', type=datetime_from_iso8601, required=False, help='TODO.')
query_entries_parser.add_argument('tag', type=str, required=False, help='TODO.')
query_entries_parser.add_argument('event', type=str, required=False, help='TODO.')
query_entries_parser.add_argument('username', type=str, required=False, help='TODO.')
query_entries_parser.add_argument('hostname', type=str, required=False, help='TODO.')
query_entries_parser.add_argument('message', type=dict, required=False, help='TODO.')
query_entries_parser.add_argument('locale', type=str, default='en', required=False, help='TODO.')

@app.route('/admindiary/options')
def options():
	with get_client(version=1) as client:
		return json.dumps(client.options()), {'Content-Type': 'application/json'}

@app.route('/admindiary/translate')
def translate():
	event_name = request.args['event']
	locale = request.args['locale']
	with get_client(version=1) as client:
		return json.dumps(client.translate(event_name, locale)), {'Content-Type': 'application/json'}

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

entry_list_model = api.model('Model', {
	'id': fields.Integer,
	'timestamp': fields.DateTime(dt_format='iso8601'),
	'username': fields.String,
	'hostname': fields.String,
	'message': fields.Raw,
	'args': fields.Raw,
	'context_id': fields.String,
	'event': fields.String,
	'comments': fields.Boolean,
})

@api.route('/entries/')
@api.doc('AdminDiaryEntry')
class AdminDiaryEntryList(Resource):
	method_decorators = (auth.login_required,)

	@api.doc('list_entries')
	@api.marshal_list_with(entry_list_model)
	@api.expect(query_entries_parser)
	def get(self):  # type: () -> typing.Tuple[typing.Dict[str, typing.Any], int]
		app.logger.debug('AdminDiaryEntryList.get()')
		args = query_entries_parser.parse_args()
		app.logger.debug(str(args))
		app.logger.debug(repr(args))
		with get_client(version=1) as client:
			entries = client.query(args.time_from, args.time_until, args.tag, args.event, args.username, args.hostname, args.message, args.locale)
			app.logger.debug(repr(entries))
			return entries

	@api.doc('create_entry')
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
	app.run(debug=DEBUG)
