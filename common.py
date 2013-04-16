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
or maybe be a monotonic counter), and also the timestamp key

- if (ZCARD timestamp) == 1 then this was the first event this second: add the timestamp
to a list, with a known name PENDING_LIST.



gather event algorithm:

- first check the SORTED_LIST for an event key

	- if found, get data from a HASH object with that key (including the
	timestampkey to get the related ZSET)

	- check number of repetitions as the ZSET score.

	- remove the grouping key from the ZSET

- if the SORTED_LIST was empty, check the PENDING_LIST to get the next timestampkey

- refill SORTED_LIST by sorting the ZSET by the hires time stored in the HASH objects.


"""

import json
from hashlib import sha1
from redis import WatchError

class Centraloger(object):
	PENDING_LIST = '__PENDING_LIST__'
	SORTED_LIST = '__SORTED_LIST__'

	def __init__(self, conn):
		self.conn = conn

	def logEvent(self, rec):
		'''Stores an event. [rec] should be a LogRecord object'''
		timestampkey = self._ts_key(rec.created)
		groupkey = self._grp_key(rec, timestampkey)

		r = self.conn.zincrby(timestampkey, groupkey, 1.0)
		if r <= 1.0:
			self.conn.hmset(groupkey, {
				'time': rec.created,
				'timestampkey': timestampkey,
				'msg': rec.msg,
				'args': json.dumps(rec.args),
			})
			if self.conn.zcard(timestampkey) <= 1:
				self.conn.rpush(self.PENDING_LIST, timestampkey)

	@staticmethod
	def _ts_key(t):
		return 'ts:%d' % int(t)

	@staticmethod
	def _grp_key(rec, timestampkey):
		return sha1(':'.join((
			rec.module,
			rec.filename,
			str(rec.lineno),
			rec.msg,
			timestampkey,
			))).hexdigest()

	def getEvent(self):
		'''processes a single event'''
		with self.conn.pipeline() as p:
			while 1:
				try:
					p.watch (self.SORTED_LIST)
					evtkey = p.lindex(self.SORTED_LIST, 0)
					if evtkey:
						# got an event key, retrieve and remove data
						evt = p.hgetall(evtkey)
						if 'timestampkey' in evt:
							evt['repeats'] = p.zscore(evt['timestampkey'], evtkey)
						p.multi()
						p.lpop(self.SORTED_LIST)
						p.delete(evtkey)
						if 'timestampkey' in evt:
							p.zrem(evt['timestampkey'], evtkey)
						p.execute()
						return evt

					# SORTED_LIST was empty, build it
					p.unwatch()
					p.watch(self.PENDING_LIST)
					timestampkey = p.lindex(self.PENDING_LIST, 0)
					if not timestampkey:
						# no more events
						return None
					p.watch(timestampkey)
					p.multi()
					p.lpop(self.PENDING_LIST)
					p.sort(timestampkey, by='*->time', store=self.SORTED_LIST)
					p.execute()
					# now retry to get first event from SORTED_LIST
				except WatchError:
					continue


