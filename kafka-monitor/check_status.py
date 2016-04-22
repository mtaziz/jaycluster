# -*- coding:utf-8 -*-

from redis import Redis
import re
import os

REGX_TYPE_DICT = {
                "update":re.compile(r"page type:update_product.*(Error)|(banned).*"),
                "get":re.compile(r"page type:index_page.*Error|(banned).*"),
            }
REGX_SPIDER_DICT = {
'amazon':re.compile(r'http://www.amazon.com/gp/product/(.*)/'),
'eastbay':re.compile(r'http://www.eastbay.com/product/model:(.*)/'),
'finishline':re.compile(r'http://www.finishline.com/store/catalog/product.jsp?productId=(.*)'),
'drugstore':re.compile(r'http://www.drugstore.com/products/prod.asp?pid=(.*)'),
'zappos':re.compile(r'http://www.zappos.com/product/(.*)'),
'6pm':re.compile(r'http://www.6pm.com/product/(.*)'),
'ashford':re.compile(r'http://www.ashford.com/us/(.*).pid')
}

def format(d, f=False):
    for k, v in d.items():
        if f:
            print("reason --> %s"%v.ljust(22))
            print("url    --> %s"%k.ljust(22))
        else:
            print("%s -->  %s"%(k.ljust(22), v))

def main(crawlid, _type="update", path=".", host="192.168.200.90"):
    redis_conn = Redis(host)
    key = "crawlid:%s"%crawlid
    total_pages = int(redis_conn.hget(key, "total_pages") or 0)
    crawled_pages = int(redis_conn.hget(key, "crawled_pages") or 0)
    failed_pages = int(redis_conn.hget(key, "failed_download_pages") or 0)
    drop_pages = int(redis_conn.hget(key, "drop_pages") or 0)
    failed_images = int(redis_conn.hget(key, "failed_download_images") or 0)
    spider_name = redis_conn.hget(key, "spiderid")
    format(redis_conn.hgetall(key))
    if drop_pages or failed_pages:
        print_if = raw_input("show the failed pages(include failed_download_pages and drop_pages)? y/n:")
        if print_if == "y":
            key = "failed_pages:%s"%crawlid
            p = redis_conn.hgetall(key)
            format(p, True)
            if failed_images:
                print_if = raw_input("show the failed download pages? y/n:")
                if print_if == "y":
                    key = "failed_images:%s"%crawlid
                    p = redis_conn.hgetall(key)
                    format(p, True)
    if (total_pages <= crawled_pages+failed_pages+drop_pages and total_pages != 0) or (total_pages < crawled_pages+failed_pages+drop_pages and total_pages == 0):
        print("finish")
        print_if = raw_input("generate the failed url file? y/n")
        if print_if == "y":
            print_to_file(redis_conn, crawlid, path, spider_name, _type)
    else:
        import datetime
        now = datetime.datetime.now()
        u_t = redis_conn.hget(key, "update_time")
        update_time = datetime.datetime.strptime(u_t, "%Y-%m-%d %H:%M:%S") if u_t else now
        if (now-update_time).seconds < 600:
            print("haven't finished")
        else:
            print("finish")
            print_if = raw_input("generate the failed url file? y/n")
            if print_if == "y":
                print_to_file(redis_conn, crawlid, path, spider_name, _type)

def print_to_file(redis_conn, crawlid, path, spider_name, _type):
    filename = os.path.join(path, "%s_%s_%s.txt"%(spider_name, crawlid, _type))
    f = open(filename, "w")
    key = "failed_pages:%s" % crawlid
    urls = redis_conn.hgetall(key)
    for url, reason in urls.items():
        if REGX_TYPE_DICT.get(_type).search(reason):
            if _type == "update":
                for regx in REGX_SPIDER_DICT:
                    mth = regx.search(url)
                    if mth:
                        f.write(mth.group(1))
            else:
                f.write(url)
    f.close()
    print os.path.abspath(filename)


if __name__ == "__main__":
    import sys
    sys.exit(main(*sys.argv[1:]))
