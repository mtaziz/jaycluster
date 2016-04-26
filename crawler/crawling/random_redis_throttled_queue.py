# -*- coding:utf-8 -*-
import random
from scutils.redis_throttled_queue import RedisThrottledQueue

class Discriptor(object):
    choicer = None
    def __init__(self):
        self.choicer = self.choice()

    def choice(self):
        while True:
            yield random.random()*self.value

    def __get__(self, instance, cls):
        a = self.choicer.next()
        return a

    def __set__(self, instance, value):
        self.value = value*2

class RandomRedisThrottledQueue(RedisThrottledQueue):
    moderation = Discriptor()


