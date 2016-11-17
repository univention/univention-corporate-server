#!/usr/bin/python
"""Unit test for univention.into_tools."""
# pylint: disable-msg=C0103,E0611,R0904
import unittest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir, 'python'))
import univention.info_tools as uit


class TestLocalizedValue(unittest.TestCase):

	"""Unit test for univention.info_tools.LocalizedValue"""

	def setUp(self):
		"""Create object."""
		self.obj = uit.LocalizedValue()
		uit.set_language('fr')

	def tearDown(self):
		"""Destroy object."""
		del self.obj

	def test_basic(self):
		"""set() and get() without locale."""
		self.obj.set('foo')
		self.assertEqual('foo', self.obj.get())

	def test_explicit_language(self):
		"""set() and get() with locale."""
		self.obj.set('foo', locale='fr')
		self.obj.set('bar', locale='en')
		self.assertEqual('foo', self.obj.get(locale='fr'))

	def test_implicit_language_set(self):
		"""set() without and get() with locale."""
		self.obj.set('foo')
		self.obj.set('bar', locale='en')
		self.assertEqual('foo', self.obj.get(locale='fr'))

	def test_default_language_set(self):
		"""set_default() and get() with locale."""
		self.obj.set_default('foo')
		self.obj.set('bar', locale='en')
		self.assertEqual('foo', self.obj.get(locale='fr'))

	def test_default_language_get(self):
		"""set_default() and get_default()."""
		self.obj.set_default('foo')
		self.obj.set('bar', locale='en')
		self.assertEqual('foo', self.obj.get_default())

	def test_missing_language(self):
		"""set() and get() with different locale."""
		self.obj.set('bar', locale='en')
		self.assertEqual('', self.obj.get(locale='fr'))


class TestLocalizedDictionary(unittest.TestCase):

	"""Unit test for univention.info_tools.LocalizedDictionary"""

	def setUp(self):
		"""Create object."""
		self.obj = uit.LocalizedDictionary()
		uit.set_language('fr')

	def tearDown(self):
		"""Destroy object."""
		del self.obj

	def test_basic(self):
		"""__setitem__() and __getitem__()."""
		self.obj['foo'] = 'bar'
		self.assertEqual('bar', self.obj['foo'])

	def test_setitem_getitem(self):
		"""__setitem__() and __getitem__()."""
		self.obj['foO'] = 'bar'
		self.assertEqual('bar', self.obj['Foo'])

	def test_default(self):
		"""__setitem__() and get(default)."""
		self.assertEqual('default', self.obj.get('foo', 'default'))

	def test_set_locale(self):
		"""set() with and get() without locale."""
		self.obj['foo[fr]'] = 'bar'
		self.assertEqual('bar', self.obj.get('foo'))
		self.assertEqual('bar', self.obj['foo'])

	def test_get_locale(self):
		"""set() without and get() with locale."""
		self.obj['foo'] = 'bar'
		self.assertEqual('bar', self.obj.get('foo[fr]'))
		self.assertEqual('bar', self.obj['foo[fr]'])

	def test_in(self):
		"""in and has_key()."""
		self.assertFalse('foo' in self.obj)
		self.assertFalse(self.obj.has_key('foo'))
		self.obj['foo'] = 'bar'
		self.assertTrue('foO' in self.obj)
		self.assertTrue(self.obj.has_key('foO'))

	def test_in_locale(self):
		"""in and has_key() with locale request."""
		self.obj['foo'] = 'bar'
		self.assertTrue('foO[fr]' in self.obj)
		self.assertTrue(self.obj.has_key('foO[fr]'))

	def test_in_locale_set(self):
		"""in and has_key() with locale set."""
		self.obj['foo[fr]'] = 'bar'
		self.assertTrue('foO' in self.obj)
		self.assertTrue(self.obj.has_key('foO'))

	def test_normalize(self):
		"""normalize()."""
		reference = {
			'foo[fr]': 'bar',
			'foo[en]': 'baz',
			'foo': 'bam',
		}
		for key, value in reference.items():
			self.obj[key] = value
		norm = self.obj.normalize('foo')
		self.assertEqual(norm, reference)

	def test_get_dict(self):
		"""get_dict()."""
		reference = {
			'foo[fr]': 'bar',
			'foo[en]': 'baz',
		}
		for key, value in reference.items():
			self.obj[key] = value
		var = self.obj.get_dict('foo')
		self.assertTrue(isinstance(var, uit.LocalizedValue))
		self.assertEqual('bar', var['fr'])
		self.assertEqual('baz', var['en'])

	def test_eq(self):
		"""__eq__ and __neq__."""
		obj = uit.LocalizedDictionary()
		self.assertEqual(self.obj, obj)
		self.assertEqual(obj, self.obj)
		self.obj['foo'] = 'bar'
		self.assertNotEqual(self.obj, obj)
		self.assertNotEqual(obj, self.obj)
		obj['foo'] = 'bar'
		self.assertEqual(self.obj, obj)
		self.assertEqual(obj, self.obj)


class TestSetLanguage(unittest.TestCase):

	"""Unit test for univention.info_tools.set_language()."""

	def setUp(self):
		"""Create objects."""
		self.lval = uit.LocalizedValue()
		self.lval['de'] = 'foo'
		self.lval['en'] = 'bar'
		self.lval.set_default('baz')
		self.ldict = uit.LocalizedDictionary()
		self.ldict['val[de]'] = 'foo'
		self.ldict['val[en]'] = 'bar'
		self.ldict['val'] = 'baz'

	def tearDown(self):
		"""Destroy objects."""
		del self.lval
		del self.ldict

	def test_global(self):
		"""Test global set_language() setting."""
		uit.set_language('de')
		self.assertEqual('foo', self.lval.get())
		self.assertEqual('foo', self.ldict['val'])
		uit.set_language('en')
		self.assertEqual('bar', self.lval.get())
		self.assertEqual('bar', self.ldict['val'])

	def test_default(self):
		"""Test default set_language() setting."""
		uit.set_language('fr')
		self.assertEqual('baz', self.lval.get())
		self.assertEqual('baz', self.ldict['val'])


if __name__ == '__main__':
	unittest.main()
