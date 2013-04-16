import sys
import logging
import redis
from common import Centraloger


_conn = redis.Redis()

def raises(f, excpt):
	try:
		f()
		return False
	except excpt:
		return True


def setup_module():
	_conn.delete(Centraloger.SORTED_LIST)
	_conn.delete(Centraloger.PENDING_LIST)

	print sys._getframe(0).f_code.co_name, 'ok.'


def test_empty_gather():
	logger = Centraloger(_conn)
	assert logger.getEvent() == None

	print sys._getframe(0).f_code.co_name, 'ok.'


def test_one_event():
	logger = Centraloger(_conn)
	logger.logEvent(logging.makeLogRecord({
		'msg': 'hi there (%s)',
		'args': ('everybody',),
		'levelno': logging.DEBUG,
	}))

	evt = logger.getEvent()
	assert evt['repeats'] == 1.0

	evt = logger.getEvent()
	assert evt == None

	print sys._getframe(0).f_code.co_name, 'ok.'


def test_repeated_event():
	logger = Centraloger(_conn)
	logger.logEvent(logging.makeLogRecord({
		'msg': 'first form (%s)',
		'args': ('first',),
		'levelno': logging.DEBUG,
	}))

	logger.logEvent(logging.makeLogRecord({
		'msg': 'second form (%s)',
		'args': ('second',),
		'levelno': logging.DEBUG,
	}))

	logger.logEvent(logging.makeLogRecord({
		'msg': 'first form (%s)',
		'args': ('third, but first',),
		'levelno': logging.DEBUG,
	}))

	evt = logger.getEvent()
	assert evt['repeats'] == 2.0
	assert evt['msg'] == 'first form (%s)'

	evt = logger.getEvent()
	assert evt['repeats'] == 1.0
	assert evt['msg'] == 'second form (%s)'

	evt = logger.getEvent()
	assert evt == None

	print sys._getframe(0).f_code.co_name, 'ok.'


if __name__ == '__main__':
	setup_module()
	test_empty_gather()
	test_one_event()
	test_repeated_event()


