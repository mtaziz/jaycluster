#coding:utf-8
import argparse
import time
import redis
import sys
from kafka_monitor_sdk import feed
from settings import REDIS_HOST, REDIS_PORT


def build_url(line, spiderid):
    if spiderid == 'amazon':
        return 'http://www.amazon.com/gp/product/%s/ref=twister_dp_update?ie=UTF8&psc=1' % line.strip()
    elif spiderid == 'eastbay':
        return 'http://www.eastbay.com/product/model:%s' % line.strip()
    elif spiderid == 'finishline':
        return 'http://www.finishline.com/store/catalog/product.jsp?productId=%s' % line.strip()
    elif spiderid == 'drugstore':
        return 'http://www.drugstore.com/products/prod.asp?pid=%s' % line.strip()
    elif spiderid == 'zappos':
        return 'http://www.zappos.com/product/%s' % line.strip()
    elif spiderid == '6pm':
        return 'http://www.6pm.com/product/%s' % line.strip()
    elif spiderid == 'ashford':
        return 'http://www.ashford.com/us/%s.pid' % line.strip()


def gen_crawlid():
    return time.strftime("%Y%m%d%H%M%S")




def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-url', type=str)
    parser.add_argument('-appid', type=str)
    parser.add_argument('-crawlid', type=str)
    parser.add_argument('-spiderid', type=str)
    parser.add_argument('-urlsfile', type=str)
    parser.add_argument('-fullurl', default=False, action='store_true')
    try:
        args = parser.parse_args()
    except:
        print('unrecognized arguments.')
        exit(1)


    crawlid = args.crawlid or gen_crawlid()

    redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


    # 更新抓取
    if args.urlsfile:
        with open(args.urlsfile) as f:
            lines_count = 0
            for line in f.readlines():
                lines_count += 1
                url = line.strip() if args.fullurl else build_url(line, args.spiderid)
                json_req = '{"url":"%s","appid":"%s","crawlid":"%s","spiderid":"%s","callback":"parse_item_update"}' % (
                    url,
                    args.appid,
                    crawlid,
                    args.spiderid
                )
                feed('settings_crawling.py', json_req)

    else:
        # add by msc
        url_list = args.url.split("     ")
        for url in url_list:
            # 一般抓取
            json_req = '{"url":"%s","appid":"%s","crawlid":"%s","spiderid":"%s","callback":"parse"}' % (
                url.strip(),
                args.appid,
                crawlid,
                args.spiderid
            )

            feed('settings_crawling.py', json_req)

    return 0

if __name__ == "__main__":
    sys.exit(main())

