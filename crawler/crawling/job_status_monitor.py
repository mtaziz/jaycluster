import time
class JobStatusMonitor(object):

    def __init__(self, spider):
        self.spider = spider
        self.redis_conn = spider.redis_conn
        self.log = spider.log

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
    def set_init_value(self,crawlid, spiderid, appid):
        self.redis_conn.hset("crawlid:%s" % crawlid, "total_pages", -1)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)

    def set_total_pages(self, crawlid, spiderid, appid,total_pages):
        self.redis_conn.hset("crawlid:%s" % crawlid, "total_pages", total_pages)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)

    def inc_crawled_pages(self, crawlid, spiderid, appid):
        self.redis_conn.hincrby("crawlid:%s" % crawlid, "crawled_pages", 1)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)
        self.inc_crawled_pages_one_worker(crawlid=crawlid, workerid=self.spider.worker_id)
        self.log("WORKER_CRAWLED_MESSAGE: {crawlid:%s,workerid:%s, %s }" % (
            crawlid,
            self.spider.worker_id,
            self.get_all_status_value_one_worker(crawlid, self.spider.worker_id)))

    def inc_crawled_pages_one_worker(self,crawlid,workerid):
        self.redis_conn.hincrby("crawlid:%s:workerid:%s" % (crawlid, workerid), "crawled_pages", 1)

    def inc_yield_pages(self, crawlid, spiderid, appid):
        self.redis_conn.hincrby("crawlid:%s" % crawlid, "yield_pages", 1)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)

    def inc_drop_pages(self, crawlid, spiderid, appid):
        self.redis_conn.hincrby("crawlid:%s" % crawlid, "drop_pages", 1)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)

    def inc_banned_pages(self, crawlid, spiderid, appid):
        self.redis_conn.hincrby("crawlid:%s" % crawlid, "banned_pages", 1)
        self._set_spiderid_and_appid(crawlid, spiderid, appid)
        self.inc_banned_pages_one_worker(crawlid=crawlid, workerid=self.spider.worker_id)
        self.log("WORKER_BANNED_MESSAGE: {crawlid:%s,workerid:%s, %s }" % (
            crawlid,
            self.spider.worker_id,
            self.get_all_status_value_one_worker(crawlid, self.spider.worker_id)))

    def inc_banned_pages_one_worker(self,crawlid, workerid):
        self.redis_conn.hincrby("crawlid:%s:workerid:%s" % (crawlid, workerid), "banned_pages", 1)

    def get_all_status_value(self, crawlid):
        return self.redis_conn.hgetall("crawlid:%s" % crawlid)

    def get_all_status_value_one_worker(self,crawlid,workerid):
        return self.redis_conn.hgetall("crawlid:%s:workerid:%s" % (crawlid, workerid))

