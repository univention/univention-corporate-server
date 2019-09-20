#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Common Python Library
#  OrderedSet
#
# Copyright 2017-2019 Univention GmbH
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

import unittest
import collections


class OrderedSet(collections.MutableSet):
	"""
	A `set()` that remembers insertion order.
	"""
	def __init__(self, iterable=None):
		raw = ((k, None) for k in iterable) if iterable else ()
		self._data = collections.OrderedDict(raw)

	@property
	def _name(self):
		return self.__class__.__name__

	def __repr__(self):
		return "{}({!r})".format(self._name, [x for x in self])

	def __len__(self):
		return len(self._data)

	def __contains__(self, key):
		return key in self._data

	def __getitem__(self, index):
		try:
			return self._data.keys()[index]
		except IndexError:
			raise IndexError("{} index out of range".format(self._name))

	def add(self, key):
		self._data[key] = None

	def update(self, sequence):
		self._data.update((k, None) for k in sequence)

	def clear(self):
		self._data.clear()

	def pop(self):
		if not self:
			raise KeyError("{} is empty".format(self._name))
		first = next(iter(self))
		self.discard(first)
		return first

	def discard(self, key):
		del self._data[key]

	def __iter__(self):
		return iter(self._data)

	def __eq__(self, other):
		if isinstance(other, OrderedSet):
			return self._data == other._data
		if isinstance(other, collections.Set):
			return set(self) == other
		return False

	def __reversed__(self):
		return OrderedSet(reversed(self._data))

	def isdisjoint(self, other):
		return bool(self & other)

	def issubset(self, other):
		return self <= other

	def issuperset(self, other):
		return self >= other

	def difference(self, other):
		return self - other

	def intersection(self, other):
		return self & other

	def symmetric_difference(self, other):
		return self ^ other

	def union(self, other):
		return self | other


class OrderedSetTest(unittest.TestCase):
	def test_empty_init(self):
		os = OrderedSet()
		self.assertEqual(len(os), 0)
		os = OrderedSet([])
		self.assertEqual(len(os), 0)

	def test_simple_init(self):
		os = OrderedSet([1])
		self.assertEqual(len(os), 1)

	def test_large_init(self):
		os = OrderedSet([1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4])
		self.assertEqual(len(os), 4)

	def test_contains(self):
		os = OrderedSet([1, 2, 3])
		self.assertIn(1, os)
		self.assertNotIn(4, os)

	def test_getitem(self):
		os = OrderedSet([1, 2, 3])
		self.assertEqual(os[0], 1)
		self.assertEqual(os[1], 2)
		self.assertEqual(os[2], 3)
		with self.assertRaises(IndexError):
			os[42]

	def test_add(self):
		os = OrderedSet([1, 2, 3])
		self.assertEqual(len(os), 3)
		os.add(3)
		self.assertIn(3, os)
		self.assertEqual(len(os), 3)
		os.add(4)
		self.assertIn(4, os)
		self.assertEqual(len(os), 4)

	def test_update(self):
		os = OrderedSet([1, 2, 3])
		self.assertEqual(len(os), 3)
		os.update([3, 4, 5, 6])
		self.assertEqual(len(os), 6)
		for x in (1, 2, 3, 4, 5, 6):
			self.assertIn(x, os)

	def test_clear(self):
		os = OrderedSet([1, 2, 3])
		os.clear()
		self.assertEqual(len(os), 0)
		for x in (1, 2, 3):
			self.assertNotIn(x, os)

	def test_pop(self):
		os = OrderedSet([1, 2, 3])
		self.assertEqual(os.pop(), 1)
		self.assertNotIn(1, os)
		self.assertEqual(len(os), 2)
		self.assertEqual(os.pop(), 2)
		self.assertNotIn(2, os)
		self.assertEqual(len(os), 1)
		self.assertEqual(os.pop(), 3)
		self.assertNotIn(3, os)
		self.assertEqual(len(os), 0)
		with self.assertRaises(KeyError):
			os.pop()

	def test_discard(self):
		os = OrderedSet([1, 2, 3])
		os.discard(2)
		self.assertNotIn(2, os)
		self.assertEqual(len(os), 2)
		for x in (1, 3):
			self.assertIn(x, os)

	def test_iter(self):
		os = OrderedSet([])
		collected = [x for x in os]
		self.assertEqual(collected, [])
		os = OrderedSet([1, 2, 3])
		collected = [x for x in os]
		self.assertEqual(collected, [1, 2, 3])
		os = OrderedSet([3, 2, 1])
		collected = [x for x in os]
		self.assertEqual(collected, [3, 2, 1])

	def test_eq_empty(self):
		os_emtpy_a = OrderedSet()
		os_emtpy_b = OrderedSet([])
		self.assertEqual(os_emtpy_a, os_emtpy_b)
		self.assertEqual(os_emtpy_a, set())
		self.assertNotEqual(os_emtpy_a, [])
		self.assertNotEqual(os_emtpy_a, ())

	def test_eq_single(self):
		os_one_a = OrderedSet([1])
		os_one_b = OrderedSet([1])
		os_one_c = OrderedSet([2])
		self.assertEqual(os_one_a, os_one_b)
		self.assertNotEqual(os_one_a, os_one_c)
		self.assertEqual(os_one_a, set([1]))
		self.assertNotEqual(os_one_a, [1])
		self.assertNotEqual(os_one_a, (1,))

	def test_eq_multiple(self):
		os_one = OrderedSet([1])
		os_multiple_a = OrderedSet([1, 2, 3])
		os_multiple_b = OrderedSet([1, 2, 3, 3])
		os_multiple_c = OrderedSet([3, 2, 1])
		os_multiple_d = OrderedSet([4, 5, 6])

		self.assertNotEqual(os_one, os_multiple_a)
		self.assertEqual(os_multiple_a, os_multiple_b)
		self.assertNotEqual(os_multiple_a, os_multiple_c)
		self.assertNotEqual(os_multiple_a, os_multiple_d)

	def test_reversed(self):
		self.assertEqual(reversed(OrderedSet([])), OrderedSet([]))
		self.assertEqual(reversed(OrderedSet([1])), OrderedSet([1]))
		self.assertEqual(reversed(OrderedSet([1, 2])), OrderedSet([2, 1]))
		self.assertEqual(reversed(OrderedSet([1, 2, 3])), OrderedSet([3, 2, 1]))
		self.assertEqual(reversed(OrderedSet([1, 2, 2, 3])), OrderedSet([3, 3, 2, 1]))

	# With the methods as tested above, several are available through
	# `collections.MutableSet`. The typical `set` operations are available
	# through `collections.Set`.

	def test_remove(self):
		os = OrderedSet([1, 2, 3])
		os.remove(2)
		self.assertNotIn(2, os)
		self.assertEqual(len(os), 2)
		with self.assertRaises(KeyError):
			os.remove(2)

	def test_is_subset(self):
		os_a = OrderedSet([1, 2, 3])
		os_b = OrderedSet([1, 2, 3, 3, 4, 5])
		self.assertTrue(os_a <= os_b)
		self.assertFalse(os_b <= os_a)
		self.assertTrue(os_a.issubset(os_b))
		self.assertFalse(os_b.issubset(os_a))
		self.assertTrue(set([1]) <= OrderedSet([1, 2]))
		self.assertTrue(OrderedSet([1]) <= set([1, 2]))

	def test_is_superset(self):
		os_a = OrderedSet([1, 2, 3])
		os_b = OrderedSet([1, 2, 3, 3, 4, 5])
		self.assertTrue(os_b >= os_a)
		self.assertFalse(os_a >= os_b)
		self.assertTrue(os_b.issuperset(os_a))
		self.assertFalse(os_a.issuperset(os_b))
		self.assertTrue(set([1, 2]) >= OrderedSet([1]))
		self.assertTrue(OrderedSet([1, 2]) >= set([1]))

	def test_union(self):
		self.assertEqual(OrderedSet() | OrderedSet(), OrderedSet())
		self.assertEqual(OrderedSet([1]) | OrderedSet([1]), OrderedSet([1]))
		self.assertEqual(OrderedSet([1]) | OrderedSet([2]), OrderedSet([1, 2]))
		self.assertEqual(OrderedSet([1, 2]) | OrderedSet([2, 3]), OrderedSet([1, 2, 3]))
		self.assertEqual(OrderedSet([1, 2]).union(OrderedSet([2, 3])), OrderedSet([1, 2, 3]))

	def test_union_set(self):
		self.assertEqual(set([1]) | OrderedSet([2]), set([1, 2]))
		self.assertEqual(OrderedSet([1]) | set([2]), OrderedSet([1, 2]))
		self.assertEqual(set([1]).union(OrderedSet([2])), set([1, 2]))
		self.assertEqual(OrderedSet([1]).union(set([2])), OrderedSet([1, 2]))

	def test_intersection(self):
		self.assertEqual(OrderedSet() & OrderedSet(), OrderedSet())
		self.assertEqual(OrderedSet([1]) & OrderedSet([1]), OrderedSet([1]))
		self.assertEqual(OrderedSet([1]) & OrderedSet([2]), OrderedSet([]))
		self.assertEqual(OrderedSet([1, 2]) & OrderedSet([2, 3]), OrderedSet([2]))
		self.assertEqual(OrderedSet([1, 2]).intersection(OrderedSet([2, 3])), OrderedSet([2]))

	def test_intersection_set(self):
		self.assertEqual(set([1, 2, 3]) & OrderedSet([2, 3, 4]), set([2, 3]))
		self.assertEqual(OrderedSet([1, 2, 3]) & set([2, 3, 4]), OrderedSet([2, 3]))
		self.assertEqual(set([1, 2, 3]).intersection(OrderedSet([2, 3, 4])), set([2, 3]))
		self.assertEqual(OrderedSet([1, 2, 3]).intersection(set([2, 3, 4])), OrderedSet([2, 3]))

	def test_difference(self):
		self.assertEqual(OrderedSet() - OrderedSet(), OrderedSet())
		self.assertEqual(OrderedSet([1]) - OrderedSet([1]), OrderedSet([]))
		self.assertEqual(OrderedSet([1]) - OrderedSet([2]), OrderedSet([1]))
		self.assertEqual(OrderedSet([1, 2]) - OrderedSet([2, 3]), OrderedSet([1]))
		self.assertEqual(OrderedSet([1, 2, 3]) - OrderedSet([4, 5]), OrderedSet([1, 2, 3]))
		self.assertEqual(OrderedSet([1, 2, 3]).difference(OrderedSet([4, 5])), OrderedSet([1, 2, 3]))

	def test_difference_set(self):
		self.assertEqual(set([1, 2, 3]) - OrderedSet([3, 4]), set([1, 2]))
		self.assertEqual(OrderedSet([1, 2, 3]) - set([3, 4]), OrderedSet([1, 2]))
		self.assertEqual(set([1, 2, 3]).difference(OrderedSet([3, 4])), set([1, 2]))
		self.assertEqual(OrderedSet([1, 2, 3]).difference(set([3, 4])), OrderedSet([1, 2]))

	def test_symmetric_difference(self):
		self.assertEqual(OrderedSet() ^ OrderedSet(), OrderedSet())
		self.assertEqual(OrderedSet([1]) ^ OrderedSet([1]), OrderedSet([]))
		self.assertEqual(OrderedSet([1]) ^ OrderedSet([2]), OrderedSet([1, 2]))
		self.assertEqual(OrderedSet([1, 2]) ^ OrderedSet([2, 3]), OrderedSet([1, 3]))
		self.assertEqual(OrderedSet([1, 4, 3]) ^ OrderedSet([4, 5]), OrderedSet([1, 3, 5]))
		self.assertEqual(OrderedSet([1, 4, 3]).symmetric_difference(OrderedSet([4, 5])), OrderedSet([1, 3, 5]))

	def test_symmetric_difference_set(self):
		self.assertEqual(set([1, 2]) ^ OrderedSet([2, 3]), set([1, 3]))
		self.assertEqual(OrderedSet([1, 2]) ^ set([2, 3]), OrderedSet([1, 3]))
		self.assertEqual(set([1, 2]).symmetric_difference(OrderedSet([2, 3])), set([1, 3]))
		self.assertEqual(OrderedSet([1, 2]).symmetric_difference(set([2, 3])), OrderedSet([1, 3]))


if __name__ == '__main__':
	unittest.main()
