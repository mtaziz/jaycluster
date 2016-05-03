from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest


class RedisRetryMiddleware(RetryMiddleware):

    def __init__(self, settings):
        RetryMiddleware.__init__(self, settings)

    @classmethod
    def from_crawler(cls, crawler):
        cls.crawler = crawler
        return cls(crawler.settings)

    @property
    def logger(self):
        return self.crawler.spider._logger

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1
        if retries <= self.max_retry_times:
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            # our priority setup is different from super
            retryreq.meta['priority'] = retryreq.meta['priority'] - 10
            return retryreq
        else:
            request.meta["url"] = request.url
            if request.meta.get("if_next_page"):
                spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'],
                                                   spiderid=request.meta['spiderid'],
                                                   appid=request.meta['appid'])
            spider.crawler.stats.set_failed_download_value(request.meta, "%s_%s"%(reason, "retry many times. "))
            self.logger.debug("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason})
            raise IgnoreRequest("max retry times")
