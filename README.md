centralog
=========

centralization logger.  tries to be fast for event generators while avoiding overwhelming the central event gatherer.

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