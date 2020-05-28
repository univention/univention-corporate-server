#!/usr/bin/python
"""Unit test for univention.into_tools."""
# pylint: disable-msg=C0103,E0611,R0904
import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir, 'python'))
import univention.info_tools as uit  # noqa E402


@pytest.fixture
def lval0():
	obj = uit.LocalizedValue()
	uit.set_language('fr')
	return obj


class TestLocalizedValue(object):

	"""Unit test for univention.info_tools.LocalizedValue"""

	def test_basic(self, lval0):
		"""set() and get() without locale."""
		lval0.set('foo')
		assert 'foo' == lval0.get()

	def test_explicit_language(self, lval0):
		"""set() and get() with locale."""
		lval0.set('foo', locale='fr')
		lval0.set('bar', locale='en')
		assert 'foo' == lval0.get(locale='fr')

	def test_implicit_language_set(self, lval0):
		"""set() without and get() with locale."""
		lval0.set('foo')
		lval0.set('bar', locale='en')
		assert 'foo' == lval0.get(locale='fr')

	def test_default_language_set(self, lval0):
		"""set_default() and get() with locale."""
		lval0.set_default('foo')
		lval0.set('bar', locale='en')
		assert 'foo' == lval0.get(locale='fr')

	def test_default_language_get(self, lval0):
		"""set_default() and get_default()."""
		lval0.set_default('foo')
		lval0.set('bar', locale='en')
		assert 'foo' == lval0.get_default()

	def test_missing_language(self, lval0):
		"""set() and get() with different locale."""
		lval0.set('bar', locale='en')
		assert '' == lval0.get(locale='fr')


@pytest.fixture
def ldict0():
	obj = uit.LocalizedDictionary()
	uit.set_language('fr')
	return obj


class TestLocalizedDictionary(object):

	"""Unit test for univention.info_tools.LocalizedDictionary"""

	def test_basic(self, ldict0):
		"""__setitem__() and __getitem__()."""
		ldict0['foo'] = 'bar'
		assert 'bar' == ldict0['foo']

	def test_setitem_getitem(self, ldict0):
		"""__setitem__() and __getitem__()."""
		ldict0['foO'] = 'bar'
		assert 'bar' == ldict0['Foo']

	def test_default(self, ldict0):
		"""__setitem__() and get(default)."""
		assert 'default' == ldict0.get('foo', 'default')

	def test_set_locale(self, ldict0):
		"""set() with and get() without locale."""
		ldict0['foo[fr]'] = 'bar'
		assert 'bar' == ldict0.get('foo')
		assert 'bar' == ldict0['foo']

	def test_get_locale(self, ldict0):
		"""set() without and get() with locale."""
		ldict0['foo'] = 'bar'
		assert 'bar' == ldict0.get('foo[fr]')
		assert 'bar' == ldict0['foo[fr]']

	def test_in(self, ldict0):
		"""in and has_key()."""
		assert 'foo' not in ldict0
		assert not ldict0.has_key('foo')  # noqa W601
		ldict0['foo'] = 'bar'
		assert 'foO' in ldict0
		assert ldict0.has_key('foO')  # noqa W601

	def test_in_locale(self, ldict0):
		"""in and has_key() with locale request."""
		ldict0['foo'] = 'bar'
		assert 'foO[fr]' in ldict0
		assert ldict0.has_key('foO[fr]')  # noqa W601

	def test_in_locale_set(self, ldict0):
		"""in and has_key() with locale set."""
		ldict0['foo[fr]'] = 'bar'
		assert 'foO' in ldict0
		assert ldict0.has_key('foO')  # noqa W601

	def test_normalize(self, ldict0):
		"""normalize()."""
		reference = {
			'foo[fr]': 'bar',
			'foo[en]': 'baz',
			'foo': 'bam',
		}
		for key, value in reference.items():
			ldict0[key] = value
		norm = ldict0.normalize('foo')
		assert norm == reference

	def test_get_dict(self, ldict0):
		"""get_dict()."""
		reference = {
			'foo[fr]': 'bar',
			'foo[en]': 'baz',
		}
		for key, value in reference.items():
			ldict0[key] = value
		var = ldict0.get_dict('foo')
		assert isinstance(var, uit.LocalizedValue) is True
		assert 'bar' == var['fr']
		assert 'baz' == var['en']

	def test_eq(self, ldict0):
		"""__eq__ and __neq__."""
		obj = uit.LocalizedDictionary()
		assert ldict0 == obj
		assert obj == ldict0
		ldict0['foo'] = 'bar'
		assert ldict0 != obj
		assert obj != ldict0
		obj['foo'] = 'bar'
		assert ldict0 == obj
		assert obj == ldict0


@pytest.fixture
def lval():
	lval = uit.LocalizedValue()
	lval['de'] = 'foo'
	lval['en'] = 'bar'
	lval.set_default('baz')
	return lval


@pytest.fixture
def ldict():
	ldict = uit.LocalizedDictionary()
	ldict['val[de]'] = 'foo'
	ldict['val[en]'] = 'bar'
	ldict['val'] = 'baz'
	return ldict


class TestSetLanguage(object):

	"""Unit test for univention.info_tools.set_language()."""

	def test_global(self, lval, ldict):
		"""Test global set_language() setting."""
		uit.set_language('de')
		assert 'foo' == lval.get()
		assert 'foo' == ldict['val']
		uit.set_language('en')
		assert 'bar' == lval.get()
		assert 'bar' == ldict['val']

	def test_default(self, lval, ldict):
		"""Test default set_language() setting."""
		uit.set_language('fr')
		assert 'baz' == lval.get()
		assert 'baz' == ldict['val']
