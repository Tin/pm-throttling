'''
Rate is calculated by minute internally, this is because gevent.spawn_later's time unit is seconds.
Rate is how much the throttle should be in the time unit. By default it's the rate per minute.

Every worker who is doing throttling should hold a copy of `Throttle` instance.
A worker should finish `chunk_size` of tasks each time and check if it should ask for more after finished it.
The `min_chunk_size` can make sure the efficiency of worker, but we shouldn't make it too big, that will affect the
accurate of throttling.
'''
from math import ceil, floor
import time

from throttling.lib import redis_conn


class Throttle(object):
    def __init__(self, namespace, rate_limit, time_unit=60, chunk_factor=0.01, min_chunk_size=None):
        self.namespace = namespace
        self.time_unit = time_unit
        self.chunk_factor = chunk_factor
        self.min_chunk_size = min_chunk_size
        self.changeRate(rate_limit)

    def changeRate(self, rate_limit):
        if not isinstance(rate_limit, basestring):
            raise Exception("rate_limit should be a string like '6000/m' or '100/s'")
        try:
            rate, unit = rate_limit.split('/')
            rate = float(rate) * self.time_unit # if time unit is second

            unit = unit.lower()
            if unit not in ('m', 's'):
                raise Exception('rate time unit %s is not supported')
            if unit.lower() == 'm':
                rate /= 60
            self.rate = int(ceil(rate))
            self.rate_limit = rate_limit
        except:
            raise Exception("Error parsing rate_limit [%s]" % rate_limit)

    def __getitem__(self, name):
        return getattr(self, name)

    def current_time_bucket(self, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        return int(floor(timestamp / self.time_unit))

    def current_time_bucket_key(self, timestamp=None):
        return "t/%s/%s" % (self.namespace, self.current_time_bucket(timestamp))

    def current_rate_count(self, timestamp=None):
        return redis_conn.redis.incr(self.current_time_bucket_key(), 0)

    def idle_seconds(self, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        start_of_next_bucket = int(floor((timestamp / self.time_unit) + 1)) * self.time_unit
        if start_of_next_bucket > timestamp:
            return start_of_next_bucket - timestamp
        else:
            return self.time_unit

    def finish_throttling(self):
        redis = redis_conn.redis
        pipeline = redis.pipeline()
        for key in redis.keys("t/%s/*"):
            pipeline.delete(key)
            if len(pipeline.command_stack) >= 100:
                pipeline.execute()
        pipeline.execute()

    def throttle_task_size(self, timestamp=None):
        current_rate_count = self.current_rate_count(timestamp)
        chunk_size = self.chunk_size
        if current_rate_count < self.rate:
            increment = min(chunk_size, self.rate - current_rate_count)
            # increment will be > 0
            new_rate_count = redis_conn.redis.incr(self.current_time_bucket_key(timestamp), increment)
            # new_rate_count will be > current_rate_count
            difference = new_rate_count - self.rate
            if difference < chunk_size:
                # When 2 worker ask for jobs together, the later one should stop asking for tasks
                return (increment - difference) if difference > 0 else increment

        return 0

    @property
    def chunk_size(self):
        chunk_size = int(self.rate * self.chunk_factor)
        if self.min_chunk_size and chunk_size < self.min_chunk_size:
            return self.min_chunk_size
        else:
            return chunk_size if chunk_size > 0 else 1
