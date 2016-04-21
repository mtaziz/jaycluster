# -*- coding:utf-8 -*-
from redis import Redis
from scutils.log_factory import LogFactory
import time

def format(d, f=False):
    for k, v in d.items():
        if f:
            print("reason:%s"%v.center(20))
            print("url:%s"%k.center(20))
        else:
            print("%s -->  %s"%(k.center(20), v))


def main_loop(crawlid,host):
    '''
    The internal while true main loop for the redis monitor
    '''
    logger = LogFactory.get_instance(json=True,
                                     name='redis_spider_logger',
                                     stdout=False,
                                     level='DEBUG',
                                     dir='logs',
                                     file='redis_spider_looger.log',
                                     bytes='10MB',
                                     backups=5)

    logger.debug("Running main loop")

    redis_conn = Redis(host)
    key = "crawlid:%s"%crawlid


    while True:
        # total_pages = int(redis_conn.hget(key, "total_pages") or 0)
        # crawled_pages = int(redis_conn.hget(key, "crawled_pages") or 0)
        # failed_pages = int(redis_conn.hget(key, "failed_download_pages") or 0)
        # drop_pages = int(redis_conn.hget(key, "drop_pages") or 0)
        # format(redis_conn.hgetall(key))
        #
        #
        # if drop_pages or failed_pages:
        #     key = "failed_pages:%s" % crawlid
        #     p = redis_conn.hgetall(key)
        #     format(p, True)
        # if total_pages == crawled_pages + failed_pages + drop_pages and total_pages != 0:
        #     print("finish")
        # else:
        #     print("haven't finished")

        for crawlkey in redis_conn.hscan_iter(key):
            print(crawlkey)
            logger.info(crawlkey)

        print '------------------------------------------------------------------------'

        time.sleep(0.1)

def main(crawlid, host="192.168.56.6"):
    main_loop(crawlid,host)



if __name__ == "__main__":
    import sys
    if len(sys.argv)>2:
        main(sys.argv[1], sys.argv[2])
    else:
        main(sys.argv[1])