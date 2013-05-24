from gevent import monkey
monkey.patch_all()
import time
from throttling import Throttle
import gevent
import logging
from throttling.lib import redis_conn


logging.getLogger().setLevel(logging.INFO)


def log(message):
    logging.info(message)


class Worker(object):
    def __init__(self, namespace, id):
        self.namespace = namespace
        self.throttle = Throttle(namespace, "60000/m", time_unit=1)
        self.id = id

    def work(self):
        log("worker %s start work" % self.id)
        namespace = self.namespace
        redis = redis_conn.redis
        while redis.llen(namespace):
            tasks_count = self.throttle.throttle_task_size()
            log("worker %s task count %s" % (self.id, tasks_count))
            if tasks_count == 0:
                idle = self.throttle.idle_seconds()
                log("sleep for %s seconds" % idle)
                time.sleep(idle)
            else:
                tokens = []
                while tasks_count > 0:
                    token = redis_conn.redis.lpop(namespace)
                    tokens.append(token)
                    tasks_count -= 1
                log("worker %s served %s tokens" % (self.id, len(tokens)))
        self.throttle.finish_throttling()

    def run(self):
        log("run worker %s" % self.id)
        return gevent.spawn(self.work)


def seeding(namespace, size):
    redis = redis_conn.redis
    pipeline = redis.pipeline()
    pipeline.delete(namespace)
    for i in range(size):
        pipeline.rpush(namespace, i)

        if len(pipeline.command_stack) >= 100:
            pipeline.execute()
    EXPIRE = 60 * 60 * 24  # 1 day
    pipeline.expire(namespace, EXPIRE)
    pipeline.execute()


if __name__ == '__main__':
    start_time = time.time()
    key = "c/1024/d/ios"
    seeding(key, 10000)
    log("finished seeding")
    greenlets = []
    for id in range(8):
        greenlets.append(Worker(key, id).run())
    gevent.joinall(greenlets)
    log('finished in %s seconds' % (time.time() - start_time))
