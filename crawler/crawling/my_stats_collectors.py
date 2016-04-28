# -*- coding:utf-8 -*-
from scrapy.statscollectors import MemoryStatsCollector

import redis
import time
from utils import RedisDict

class MyStatsCollector(MemoryStatsCollector):
    """
        use redis to collect stats.
    """
    def __init__(self, crawler):
        super(MyStatsCollector, self).__init__(crawler)
        self.crawler = crawler
        self._setup_redis()
        self._stats = RedisDict(self.redis_conn, crawler)

        # self.logger = LogFactory.get_instance(json=True,
        #                              name="spider-stats-logger",
        #                              stdout=False,
        #                              level="info",
        #                              dir="logs",
        #                              file="spider-stats.log",
        #                              bytes="10M",
        #                              backups=3)

    def _persist_stats(self, stats, spider):
        self.spider_stats[spider.name] = stats

    def _setup_redis(self):
        conn = redis.Redis(host=(self.crawler.settings.get("REDIS_HOST") or "localhost"), port=(self.crawler.settings.get("REDIS_PORT") or 6379))
        self.redis_conn = conn

    def _set_spiderid_and_appid(self, crawlid, spiderid, appid):
        self.redis_conn.hmset(
            "crawlid:%s" % crawlid,
            {
                "crawlid": crawlid,
                "spiderid": spiderid,
                "appid": appid,
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )

    def inc_invalidate_property_value(self, crawlid, appid, spiderid, url, reason):
        self.redis_conn.hincrby("crawlid:%s" % crawlid, "invalidate_pages", 1)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)
        self.set_invalidate_property_pages(crawlid, url, reason)

    def set_invalidate_property_pages(self, crawlid, url, reason):
        self.redis_conn.hset("invalidate_pages:%s" % crawlid, url, reason)

    def set_failed_download_value(self, meta, reason=None, flag=False):
        """
        auto increase failed download pages
        :param crawlid:
        :return: None
        """
        if flag:
            self.redis_conn.hset("crawlid:%s" % meta.get('crawlid'), "failed_download_pages", 1)
        else:
            self.redis_conn.hincrby("crawlid:%s" % meta.get('crawlid'), "failed_download_pages", 1)
        self._set_spiderid_and_appid(meta.get('crawlid'), meta.get('spiderid'), meta.get('appid'))
        self.set_failed_download_page(meta.get('crawlid'), meta.get('url'), reason)

    def set_failed_download_images(self, meta, reason=None):

        self.redis_conn.hincrby("crawlid:%s" % meta.get('crawlid'), "failed_download_images", 1)
        self._set_spiderid_and_appid(meta.get('crawlid'), meta.get('spiderid'), meta.get('appid'))
        self.set_failed_download_images_url(meta.get('crawlid'), meta.get('url'), reason)

    def set_failed_download_images_url(self, crawlid, url, reason):
        self.redis_conn.hset("failed_images:%s" % crawlid, url, reason)

    def set_failed_download_page(self, crawlid, url, reason):
        self.redis_conn.hset("failed_pages:%s"%crawlid, url, reason)

    def set_init_value(self, crawlid, spiderid, appid, total_pages=-1):
        # add an alternative argument total_pages, it can control the output total_pages without modify other source code add bymasc
        if total_pages:
            self.redis_conn.hset("crawlid:%s" % crawlid, "total_pages", total_pages)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)

    def inc_total_pages(self, crawlid, spiderid, appid, num=1):
        """
        auto increace total pages add by msc
        :param crawlid: crawl ID
        :return: None
        """

        self.redis_conn.hincrby("crawlid:%s" % crawlid, "total_pages", num)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)

        msg={}
        msg["spiderid"] = spiderid
        msg["crawlid"] = crawlid
        msg["total_pages"] = int(self.redis_conn.hget(crawlid,"total_pages") or 0)
        self.crawler.spider._logger.info(msg)
        print msg

    def set_total_pages(self, crawlid, spiderid, appid, num=1):
        self.redis_conn.hset("crawlid:%s" % crawlid, "total_pages", num)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)

        msgdict = {}
        msgdict["msg"]["spiderid"] = spiderid
        msgdict["msg"]["crawlid"] = crawlid
        msgdict["msg"]["total_pages"] = int(self.redis_conn.hget(crawlid, "total_pages") or 0)

        self.crawler.spider._logger.info(msgdict)
        print msgdict


    def inc_crawled_pages(self, crawlid, spiderid, appid):
        self.redis_conn.hincrby("crawlid:%s" % crawlid, "crawled_pages", 1)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)
        self.inc_crawled_pages_one_worker(crawlid=crawlid, workerid=self.crawler.spider.worker_id)

        #msgvalue= {"spiderid":spiderid,"crawlid":crawlid,"workerid":self.crawler.spider.worker_id,"workerid_status":self.get_all_status_value_one_worker(crawlid, self.crawler.spider.worker_id)}
        msgvalue= {"spiderid":spiderid,"crawlid":crawlid,"workerid":self.crawler.spider.worker_id}
        msgvalue.update(self.get_all_status_value_one_worker(crawlid, self.crawler.spider.worker_id))
        msgdict = {"CrawMsg":msgvalue}
        msg = "WORKER_CRAWLED_MESSAGE"

        self.crawler.spider._logger.info(msg,msgdict)
        # self.crawler.spider._logger.info("WORKER_CRAWLED_MESSAGE: {crawlid:%s,workerid:%s, %s }" % (
        #     crawlid,
        #     self.crawler.spider.worker_id,
        #     self.get_all_status_value_one_worker(crawlid, self.crawler.spider.worker_id)))

    def inc_crawled_pages_one_worker(self, crawlid, workerid):
        self.redis_conn.hincrby("crawlid:%s:workerid:%s" % (crawlid, workerid), "crawled_pages", 1)

    def inc_yield_pages(self, crawlid, spiderid, appid):
        self.redis_conn.hincrby("crawlid:%s" % crawlid, "yield_pages", 1)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)

    def inc_drop_pages(self, crawlid, spiderid, appid, url=None, worker_id=None, page_type="unknow"):
        self.redis_conn.hincrby("crawlid:%s" % crawlid, "drop_pages", 1)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)
        self.set_failed_download_page(crawlid, url, "page type:%s. the url banned many times by %s to drop"%(page_type, worker_id))

    def inc_banned_pages(self, crawlid, spiderid, appid):
        self.redis_conn.hincrby("crawlid:%s" % crawlid, "banned_pages", 1)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)
        self.inc_banned_pages_one_worker(crawlid=crawlid, workerid=self.crawler.spider.worker_id)

        #msgvalue= {"spiderid":spiderid,"crawlid":crawlid,"workerid":self.crawler.spider.worker_id,"workerid_status":self.get_all_status_value_one_worker(crawlid, self.crawler.spider.worker_id)}
        msgvalue= {"spiderid":spiderid,"crawlid":crawlid,"workerid":self.crawler.spider.worker_id}
        msgvalue.update(self.get_all_status_value_one_worker(crawlid, self.crawler.spider.worker_id))
        msgdict = {"BanMes":msgvalue}
        msg = "WORKER_BANNED_MESSAGE"
        self.crawler.spider._logger.info(msg,msgdict)


    def inc_banned_pages_one_worker(self, crawlid, workerid):
        self.redis_conn.hincrby("crawlid:%s:workerid:%s" % (crawlid, workerid), "banned_pages", 1)

    def get_all_status_value(self, crawlid):
        return self.redis_conn.hgetall("crawlid:%s" % crawlid)

    def get_all_status_value_one_worker(self, crawlid, workerid):
        valuedict = self.redis_conn.hgetall("crawlid:%s:workerid:%s" % (crawlid, workerid))
        for key in valuedict:
            valuedict[key] = int(valuedict[key] or 0)
        valuedict["banpercent"] = "%.2f" % (float(valuedict["banned_pages"] * 100)/float(valuedict["crawled_pages"] + valuedict["banned_pages"]+1))
        return valuedict
        #return self.redis_conn.hgetall("crawlid:%s:workerid:%s" % (crawlid, workerid))



