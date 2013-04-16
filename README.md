centralog
=========

centralization logger.  tries to be fast for event generators while avoiding overwhelming the central event gatherer.

Events are temporarily stored in a Redis server. each event gets a timestamp, repeated events within the same second are stored only once; but recorded how many times occured within the second.

a "gatherer" process picks events in timestamp order, deleting them from the Redis server.  From there they could be stored on a more manageable and potentially slower system, like a conveniently-indexed SQL table.



report event algorithm:

- get a timestamp key from the current second.

- get an event grouping key. should be the same for repeating events.  for example a hash of (module,file,line,msg)

- ZINCRBY timestamp 1 groupkey

- if the result is >1, it's a repeated event, end here

- if the result is 1, it's the first time we see this event on this second, store the event data using the grouping key.  include a higher resolution time (miliseconds, or maybe be a monotonic counter), and also the timestamp key

- if (ZCARD timestamp) == 1 then this was the first event this second: add the timestamp to a list, with a known name PENDING_LIST.



gather event algorithm:

- first check the SORTED_LIST for an event key

	- if found, get data from a HASH object with that key (including the
	timestampkey to get the related ZSET)

	- check number of repetitions as the ZSET score.

	- remove the grouping key from the ZSET

- if the SORTED_LIST was empty, check the PENDING_LIST to get the next timestampkey

- refill SORTED_LIST by sorting the ZSET by the hires time stored in the HASH objects.

