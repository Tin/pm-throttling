import unittest
from throttling import Throttle

from throttling.lib import redis_conn


class ThrottlingTest(unittest.TestCase):
    def setUp(self):
        self.throttle_namespace = "c/1002/d/ios"

    def tearDown(self):
        redis_conn.redis.flushall()

    def test_initialize_throttle_shold_have_default_time_unit(self):
        rate_limit = "6000/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        self.assertEquals(60, t.time_unit)

    def test_throttle_should_tell_rate_when_rate_unit_is_minute(self):
        rate_limit = "6000/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        self.assertEquals(6000, t.rate)

    def test_throttle_should_tell_rate_when_rate_unit_is_minute_when_its_small(self):
        rate_limit = "1/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        self.assertEquals(1, t.rate)

    def test_throttle_should_tell_rate_when_rate_unit_is_second(self):
        rate_limit = "100/s"
        t = Throttle(self.throttle_namespace, rate_limit)
        self.assertEquals(6000, t.rate)

    def test_throttle_rate_should_be_integer_when_its_small(self):
        rate_limit = "0.001/s"
        t = Throttle(self.throttle_namespace, rate_limit)
        self.assertEquals(1, t.rate)

    def test_throttle_rate_should_be_integer(self):
        rate_limit = "0.001/s"
        t = Throttle(self.throttle_namespace, rate_limit)
        timestamp = 600.19095
        self.assertEquals(10, t.current_time_bucket(timestamp))
        timestamp = 600.99095
        self.assertEquals(10, t.current_time_bucket(timestamp))

    def test_throttle_should_tell_chunk_size(self):
        rate_limit = "60000/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        self.assertEquals(600, t.chunk_size)

    def test_throttle_should_able_to_limit_min_chunk_size(self):
        rate_limit = "60000/m"
        t1 = Throttle(self.throttle_namespace, rate_limit, min_chunk_size=1000)
        self.assertEquals(1000, t1.chunk_size)
        t2 = Throttle(self.throttle_namespace, rate_limit, min_chunk_size=100)
        self.assertEquals(600, t2.chunk_size)

    def test_throttle_current_bucket_key(self):
        rate_limit = "60000/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        timestamp = 600
        self.assertEquals("t/c/1002/d/ios/10", t.current_time_bucket_key(timestamp))

    def test_throttle_should_tell_current_rate_count(self):
        rate_limit = "60000/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        self.assertEquals(0, t.current_rate_count())

    def test_asking_for_tasks_should_give_a_chunk_and_change_current_rate_count(self):
        rate_limit = "60000/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        # chunk size is 600
        self.assertEquals(600, t.throttle_task_size())

    def test_asking_for_tasks_when_it_close_to_rate_limit(self):
        rate_limit = "60000/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        timestamp = 600
        redis_conn.redis.set(t.current_time_bucket_key(timestamp), 59999)
        self.assertEquals(60000-59999, t.throttle_task_size(timestamp))

    def test_asking_for_tasks_when_it_exceed_rate_limit(self):
        rate_limit = "60000/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        timestamp = 600
        redis_conn.redis.set(t.current_time_bucket_key(timestamp), 60001)
        self.assertEquals(0, t.throttle_task_size(timestamp))

    def test_asking_for_tasks_should_give_a_chunk_and_change_current_rate_count_when_rate_is_small(self):
        rate_limit = "1/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        # chunk size is 600
        self.assertEquals(1, t.throttle_task_size())

    def test_throttle_should_tell_how_long_it_should_be_idle(self):
        rate_limit = "60000/m"
        t = Throttle(self.throttle_namespace, rate_limit)
        self.assertEquals(60, t.idle_seconds(600))
        self.assertEquals(59, t.idle_seconds(601))
        self.assertEquals(1, t.idle_seconds(599))
