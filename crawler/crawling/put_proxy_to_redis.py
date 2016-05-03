# -*- coding:utf-8 -*-

from settings import REDIS_HOST
from redis import Redis
import time
from fetch_free_proxyes import fetch_all

class ProxyRedisRepository:
    proxy_key = "proxy:addr:port"

    def __init__(self, host, port=6379, key=None):
        self.redis_conn = Redis(host, port)
        if key:
            self.proxy_key = key


    def pop(self):
        pipe = self.redis_conn.pipeline()
        pipe.multi()
        pipe.zrange(self.proxy_key, 0, 0).zremrangebyrank(self.proxy_key, 0, 0)
        results, count = pipe.execute()
        if results:
            return "http://"+results[0]

    def push(self, value):
        self.redis_conn.zadd(self.proxy_key, value, time.time())

    def pushall(self, values):
        self.redis_conn.zadd(self.proxy_key, **values)

    def __len__(self):
        return self.redis_conn.zcard(self.proxy_key)

    def updateProxyAddr(self):
        #lst = ["12222:22", "3434:33"]
        self.pushall(dict(zip(fetch_all(), self._yield())))

    def _yield(self):
        while True:
            yield time.time()

    def fetchall(self):
        return self.redis_conn.zrange(self.proxy_key, 0, -1)

if __name__ == "__main__":
    while True:
        rep = ProxyRedisRepository(REDIS_HOST)
        length = len(rep)
        print length
        if length<200:
            rep.updateProxyAddr()
        else:
            time.sleep(60)