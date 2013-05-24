pm-throttling
=============

poor-man's throttling in python, for throttling with distributed workers (multiple process or multiple server instances)

Rate is calculated by minute internally, this is because gevent.spawn_later's time unit is seconds.
Rate is how much the throttle should be in the time unit. By default it's the rate per minute.

Every worker who is doing throttling should hold a copy of `Throttle` instance.
A worker should finish `chunk_size` of tasks each time and check if it should ask for more after finished it.
The `min_chunk_size` can make sure the efficiency of worker, but we shouldn't make it too big, that will affect the
accurate of throttling.
