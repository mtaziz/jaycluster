# -*- coding:utf-8 -*-

from redis import Redis
import re
import os
import argparse

REGX_TYPE_DICT = {
                "update":re.compile(r"(page type:update_product.*banned|Error).*"),
                "get":re.compile(r"(page type:index_page.*banned|Error).*"),
            }
REGX_404 = re.compile(r"404")
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
        print_if = raw_input("show the failed pages(include failed_download_pages and drop_pages)? y/n default n:")
        if print_if == "y":
            key = "failed_pages:%s"%crawlid
            p = redis_conn.hgetall(key)
            format(p, True)
            if failed_images:
                print_if = raw_input("show the failed download pages? y/n: default n:")
                if print_if == "y":
                    key = "failed_images:%s"%crawlid
                    p = redis_conn.hgetall(key)
                    format(p, True)
    if (total_pages <= crawled_pages+failed_pages+drop_pages and total_pages != 0) or (total_pages < crawled_pages+failed_pages+drop_pages and total_pages == 0):
        print("task %s have finished"%crawlid)
        print_if = raw_input("generate the failed url file? y/n default n:")
        if print_if == "y":
            print_to_file(redis_conn, crawlid, path, spider_name, _type)
    else:
        import datetime
        now = datetime.datetime.now()
        u_t = redis_conn.hget(key, "update_time")
        update_time = datetime.datetime.strptime(u_t, "%Y-%m-%d %H:%M:%S") if u_t else now
        if (now-update_time).seconds < 600:
            print("task %s haven't finished"%crawlid)
        else:
            print("task %s have finished"%crawlid)
            print_if = raw_input("generate the failed to recycle url file? y/n default n:")
            if print_if == "y":
                print_to_file(redis_conn, crawlid, path, spider_name, _type)

def print_to_file(redis_conn, crawlid, path, spider_name, _type):
    url_404_list = []
    filename = os.path.join(path, "%s_%s_%s.txt"%(spider_name, crawlid, _type))
    f = open(filename, "w")
    key = "failed_pages:%s" % crawlid
    urls = redis_conn.hgetall(key)
    for url, reason in urls.items():
        mth = REGX_SPIDER_DICT[spider_name].search(url)
        if REGX_TYPE_DICT.get(_type).search(reason):
            if _type == "update":
                if mth:
                    f.write(mth.group(1)+"\n")
            else:
                f.write(url)
        elif REGX_404.search(reason) and _type == "update":
            url_404_list.append(mth.group(1) + "\n")
    f.close()
    print os.path.abspath(filename)
    if url_404_list:
        input = raw_input("generate the 404 not found error page url? y/n default n:")
        if input == "y":
            filename_404 = os.path.join(path, "%s_%s_404.txt"%(spider_name, crawlid))
            open(filename_404, "w").writelines(url_404_list)
            print os.path.abspath(filename_404)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="usage: %prog [options]")
    parser.add_argument("-t", "--type", default="update", choices=["update", "get"], help="crawler type")
    parser.add_argument("--host", default="192.168.200.90", help="redis host")
    parser.add_argument("crawlid", nargs="+", help="crawl id")
    parser.add_argument("-p", "--path", default=".", help="the path to generate a file")
    args = parser.parse_args();
    for crawlid in args.crawlid:
        main(crawlid=crawlid, path=args.path, host= args.host, _type=args.type)