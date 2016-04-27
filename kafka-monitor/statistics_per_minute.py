# -*- coding:utf-8 -*-
from redis import Redis

from bottle import route, run, request
redis_conn = Redis("192.168.200.58")
keys = "amazon_*:count_per_minute"

@route("/")
def index():
    return redis_conn.keys(keys)

@route("/pi")


