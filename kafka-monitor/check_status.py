# -*- coding:utf-8 -*-

from redis import Redis

def format(d):
    for k, v in d.items():
        print("%s -->  %s"%(k, v))

def main(crawlid, host="192.168.200.90"):
    redis_conn = Redis(host)
    key = "crawlid:%s"%crawlid
    total_pages = int(redis_conn.hget(key, "total_pages") or 0)
    crawled_pages = int(redis_conn.hget(key, "crawled_pages") or 0)
    failed_pages = int(redis_conn.hget(key, "failed_download_pages") or 0)
    drop_pages = int(redis_conn.hget(key, "drop_pages") or 0)
    print(format(redis_conn.hgetall(key)))
    if total_pages == crawled_pages+failed_pages+drop_pages and total_pages != 0 :
        print("finish")
    else:
        print("haven't finished")

if __name__ == "__main__":
    import sys
    if len(sys.argv)>2:
        main(sys.argv[1], sys.argv[2])
    else:
        main(sys.argv[1])
