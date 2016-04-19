# -*- coding:utf-8 -*-

from redis import Redis

def main(crawlid, host="192.168.200.90"):
    redis_conn = Redis(host)
    key = "crawlid:%s"%crawlid
    type = redis_conn.hget(key, "type")
    if type == "update":
        total_pages = redis_conn.hget(key, "total_pages")
        crawled_pages = redis_conn.hget(key, "crawled_pages")
        print(redis_conn.hgetall(key))
        if total_pages == crawled_pages:
            print("finish")
            return
    if type == "get":
        total_pages = redis_conn.hget(key, "total_pages")
        crawled_pages = redis_conn.hget(key, "crawled_pages")
        print(redis_conn.hgetall(key))
        if int(total_pages) == int(crawled_pages)+1:
            print("finish")
            return
    else:
        print("haven't started")

if __name__ == "__main__":
    import sys
    if len(sys.argv)>2:
        main(sys.argv[1], sys.argv[2])
    else:
        main(sys.argv[1])
