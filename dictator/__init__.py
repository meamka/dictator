# coding: utf-8
"""
Dictator is a tiny library for Robots™ to work with Redis as a Dict.

Dictator handles Redis command to make work with database as a dict-like object.

.. codeauthor:: Andrey Maksimov <meamka@ya.ru>

Usage example:

>>> from dictator import Dictator
>>> dc = Dictator()
>>> dc['Planets'] = ['Mercury', 'Venus', 'Earth', 'Mars']
>>> dc['Stars'] = ['Sun']
>>> dc.get('Stars')
['Sun']
>>> len(dc)
2
>>> dc.pop('Planets')
['Mercury', 'Venus', 'Earth', 'Mars']
>>> del dc['Stars']

"""

import logging

import redis

logger = logging.getLogger(__name__)


class Dictator(object):
    """

        >>> dct = Dictator(host='localhost', port=6379, db=0)
        >>> len(dct)
        0
        >>> dct['key'] = 'the Value'
        >>> len(dct)
        1
        >>> dct['key']
        'the Value'
        >>> del dct['key']

    """

    def __init__(self, host='localhost', port=6379, db=0, **kwargs):
        self.host = host
        self.port = port
        self.db = db
        self._redis = redis.Redis(host=host, port=port, db=db, **kwargs)

    def __delitem__(self, key):
        """Delete one or more keys specified by ``key``

        :param key: key to delete
        :type key: str
        :return:
        """
        logger.debug('deleting %s', key)
        return self._redis.delete(key)

    def __getitem__(self, item):
        """Return the value at key ``item`` or None if item doesn't exists

        :param item:
        :return:
        """
        logger.debug('call __getattr__ %s', item)
        key_type = self._redis.type(item)
        if key_type == 'hash':
            return self._redis.hgetall(item)
        elif key_type == 'list':
            return self._redis.lrange(item, 0, -1)
        elif key_type == 'set':
            return self._redis.smembers(item)
        elif key_type == 'zset':
            return self._redis.zrange(item, 0, -1)
        else:
            return self._redis.get(item)

    def __setitem__(self, key, value):
        """Set the value at key ``key`` to ``value``

        :param key:
        :param value:
        :return:
        """
        logger.debug('call __setattr__ %s', key)
        if isinstance(value, (tuple, list)):
            self._redis.delete(key)
            self._redis.rpush(key, *value)
        elif isinstance(value, dict):
            self._redis.hmset(key, value)
        else:
            self._redis.set(key, value)

    def __iter__(self):
        """Return iterator over db's keys

        :return:
        """
        return self.iterkeys()

    def __len__(self):
        """Return number of items in db

        >>> dc = Dictator()
        >>> len(dc)
        0
        >>> dc['a'] = 'a'
        >>> len(dc)
        1
        >>> del dc['a']
        >>> len(dc)
        0

        :return: number of items in db
        :rtype: int
        """
        return len(self.keys())

    def set(self, key, value):
        """Set the value at key ``key`` to ``value``

        >>> dc = Dictator()
        >>> dc['s0'] = 'string value'
        >>> dc['s0']
        'string value'
        >>> dc.set('l0', ['abc', 123])
        >>> dc['l0']
        ['abc', '123']
        >>> del dc['s0']
        >>> del dc['l0']

        :param key: hashable value
        :param value:
        :return:
        """
        self.__setitem__(key, value)

    def get(self, key, default=None):
        """Return the value at key ``key``, or default value ``default`` which is None by default.

        >>> dc = Dictator()
        >>> dc['l0'] = [1, 2, 3, 4]
        >>> dc.get('l0')
        ['1', '2', '3', '4']
        >>> dc['l0']
        ['1', '2', '3', '4']
        >>> del dc['l0']

        :param key: key of value to return
        :type key: str
        :param default:
        :type default: Any
        :return: value of given key
        """
        return self.__getitem__(key) or default

    def pop(self, key, default=None):
        """Remove and return the last item of the list ``key``. If key doesn't exists it return ``default``.

        >>> dc = Dictator()
        >>> dc['l0'] = [1, 2, 3, 4]
        >>> dc.pop('l0')
        ['1', '2', '3', '4']
        >>> dc.pop('l1', 'empty')
        'empty'

        :param key:
        :param default:
        :return:
        """
        value = self.get(key, default)
        self._redis.delete(key)
        return value

    def keys(self, pattern=None):
        """Returns a list of keys matching ``pattern``. By default return all keys.

        >>> dc = Dictator()
        >>> dc['l0'] = [1, 2, 3, 4]
        >>> dc['s0'] = 'string value'
        >>> dc.keys()
        ['l0', 's0']
        >>> dc.keys('h*')
        []
        >>> del dc['l0']
        >>> del dc['s0']

        :param pattern: key pattern
        :type pattern: str
        :return: list of keys in db
        :rtype: list of str
        """
        if pattern is None:
            pattern = '*'

        return self._redis.keys(pattern=pattern)

    def items(self):
        """Return list of tuples of keys and values in db

        >>> dc = Dictator()
        >>> dc['l0'] = [1, 2, 3, 4]
        >>> dc.items()
        [('l0', ['1', '2', '3', '4'])]
        >>> del dc['l0']

        :return: list of tuple
        """
        return [(key, self.get(key)) for key in self.keys()]

    def values(self):
        """Return list of values in db

        >>> dc = Dictator()
        >>> dc['l0'] = [1, 2, 3, 4]
        >>> dc.items()
        [('l0', ['1', '2', '3', '4'])]
        >>> del dc['l0']

        :return: list of tuple

        :return:
        """
        return [self.get(key) for key in self.keys()]

    def iterkeys(self, match=None, count=1):
        """Return an iterator over the db's keys.
        ``match`` allows for filtering the keys by pattern.
        ``count`` allows for hint the minimum number of returns.

        >>> dc = Dictator()
        >>> dc['1'] = 'abc'
        >>> dc['2'] = 'def'
        >>> dc['3'] = 'ghi'
        >>> itr = dc.iterkeys()
        >>> type(itr)
        <type 'generator'>
        >>> list(reversed([item for item in itr]))
        ['1', '2', '3']
        >>> del dc['1']
        >>> del dc['2']
        >>> del dc['3']

        :param match: pattern to filter keys
        :type match: str
        :param count: minimum number of returns
        :type count: int
        :return: iterator over key.
        :return: iterator
        """
        if match is None:
            match = '*'
        for key in self._redis.scan_iter(match=match, count=count):
            yield key

    def iteritems(self, match=None, count=1):
        """Return an iterator over the db's (key, value) pairs.
        ``match`` allows for filtering the keys by pattern.
        ``count`` allows for hint the minimum number of returns.


        :param match: pattern to filter keys
        :type match: str
        :param count: minimum number of returns
        :type count: int
        :return: iterator over key, value pairs.
        :return: iterator
        """
        if match is None:
            match = '*'
        for key in self._redis.scan_iter(match=match, count=count):
            yield key, self.get(key)
