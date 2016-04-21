# -*- coding:utf-8 -*-

from redis import Redis

def format(d, f=False):
    for k, v in d.items():
        if f:
            print("reason:%s"%v.center(30))
            print("url:%s"%k.center(30))
        else:
            print("%s -->  %s"%(k.center(30), v))

def main(crawlid, host="192.168.200.90"):
    redis_conn = Redis(host)
    key = "crawlid:%s"%crawlid
    total_pages = int(redis_conn.hget(key, "total_pages") or 0)
    crawled_pages = int(redis_conn.hget(key, "crawled_pages") or 0)
    failed_pages = int(redis_conn.hget(key, "failed_download_pages") or 0)
    drop_pages = int(redis_conn.hget(key, "drop_pages") or 0)
    format(redis_conn.hgetall(key))
    if drop_pages or failed_pages:
        print_if = raw_input("wheather print the failed pages or not y/n:")
        if print_if == "n":
            pass
        else:
            key = "failed_pages:%s"%crawlid
            p = redis_conn.hgetall(key)
            format(p, True)
    if total_pages <= crawled_pages+failed_pages+drop_pages and total_pages != 0 :
        print("finish")
    else:
        import datetime
        now = datetime.datetime.now()
        u_t = redis_conn.hget(key, "update_time")
        update_time = datetime.datetime.strptime(u_t, "%Y-%m-%d %H:%M:%S") if u_t else now
        if (now-update_time).seconds < 600:
            print("haven't finished")
        else:
            print("finish")

if __name__ == "__main__":
    import sys
    if len(sys.argv)>2:
        main(sys.argv[1], sys.argv[2])
    else:
        main(sys.argv[1])
