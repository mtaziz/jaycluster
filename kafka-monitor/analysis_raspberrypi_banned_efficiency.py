# -*- coding:utf-8 -*-
from redis import Redis

def analysis(crawlid, host="192.168.200.90"):
    redis_conn = Redis(host)
    key = "crawlid:%s:workerid:*"%crawlid
    keys = sorted(redis_conn.keys(key))
    key_total = "crawlid:%s"%crawlid
    total_pages = int(redis_conn.hget(key_total, "total_pages"))
    print("抓取成功与总抓取量(成功的与被ban的)之比\n")
    for key in keys:
        crawled = float(redis_conn.hget(key, "crawled_pages")) or 0.0
        banned = float(redis_conn.hget(key, "banned_pages")) or 0.0
        print key[-7:-4], ">>>>",  "%.2f%%"%(crawled*100/(crawled+banned))
    print("抓取成功与各自份额之比\n")
    for key in keys:
        crawled = float(redis_conn.hget(key, "crawled_pages")) or 0.0
        print key[-7:-4], ">>>>", "%.2f%%"%(crawled*100/total_pages*len(keys))


if __name__ == "__main__":
    import sys
    if len(sys.argv)>2:
        analysis(sys.argv[1], sys.argv[2])
    else:
        analysis(sys.argv[1])