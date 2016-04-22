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


def main_loop(host):
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

    conn = Redis(host)


    crawlerdict = {}

    while True:
        keys = conn.keys('crawlid:*')
        for key in keys:
            if len(key.split(":")) == 2:
                elements = key.split(":")
                crawlid = elements[1]
                values = conn.hgetall(key)
                updatetime = values['update_time']
                if key not in crawlerdict:
                    countnum = 0
                    countlist = [updatetime, countnum]
                    crawlerdict[key] = countlist
                elif crawlerdict[key][0] == updatetime:
                    if crawlerdict[key][1] == 3:
                        print 'crawlid:', crawlid, '\t', 'it finished'
                        continue
                    else:
                        crawlerdict[key][1] += 1
                else:
                    crawlerdict[key][0] = updatetime


        time.sleep(0.1)

def main(host="192.168.200.90"):
    main_loop(host)



if __name__ == "__main__":
    import sys
    if len(sys.argv)==2:
        main(sys.argv[1])
    else:
        main()