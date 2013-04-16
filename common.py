# -*- coding: utf-8 -*-
"""

To avoid bottlenecks, events are logged in a easily shard-eable scheme:


report event algorithm:

- get a timestamp key from the current second.

- get an event grouping key. should be the same for repeating events.  for example
a hash of (module,file,line,msg)

- ZINCRBY timestamp 1 groupkey

- if the result is >1, it's a repeated event, end here

- if the result is 1, it's the first time we see this event on this second, store the
event data using the grouping key.  include a higher resolution time (miliseconds,
or maybe be a monotonic counter)
		HMSET grouping "time" hirestime "msg" msg "args" jsonencode(args)

- if (ZCARD timestamp) == 1 then this was the first event this second: add the timestamp
to a list.



gather event algorithm:

on a transaction:

- pop the first timestamp key from the pending list

- sort the events on this second:
	SORT timestamp BY *->time GET *->msg GET *->args
	(maybe using STORE to avoid reading everything at once?)

- clear the timestamp key

"""

import json
from hashlib import sha1

class Centraloger(object):

	def __init__(self, conn):
		self.conn = conn

	def logEvent(rec):
		'''Stores an event. [rec] should be a LogRecord object'''
		timestampkey = self._ts_key(rec.created)
		groupkey = self._grp_key(rec)

		r = self.conn.zincrby(timestampkey, 1, groupkey)
		if f <= 1:
			self.conn.hmset(groupkey, {
				'time': rec.created,
				'msg': rec.msg,
				'args': json.dumps(reg.args),
			})
			if self.conn.zcard(timestampkey) <= 1:
				self.conn.rpush(PENDING_LIST, timestampkey)

	@staticmethod
	def _ts_key(t):
		return 'ts:%d' % int(t)

	@staticmethod
	def _grp_key(rec):
		return sha1(':'.join((
			rec.module,
			rec.filename,
			str(rec.lineno),
			rec.msg))).hexdigest()


	def getEvent():
		'''processes a single event; returns (msg, args)'''
		with self.conn.pipeline() as p:
			p.watch (SORTED_LIST)
			evtkey = p.lpop(SORTED_LIST)
			if evtkey:
				return p.hmget(evtkey, 'msg', 'args')
			# SORTED_LIST was empty, build it

			p.watch(PENDING_LIST)
			timestampkey = lpop(PENDING_LIST)
			if not timestampkey:
				# no more events
				return None
			p.watch(timestampkey)
			p.multi()
			p.sort(timestampkey, by='*->time', store=SORTED_LIST)
			p.delete(timestampkey)
			p.execute()


