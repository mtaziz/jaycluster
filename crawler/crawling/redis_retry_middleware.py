from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest
from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
        ConnectionRefusedError, ConnectionDone, ConnectError, \
        ConnectionLost, TCPTimedOutError
from scrapy.xlib.tx import ResponseFailed


class RedisRetryMiddleware(RetryMiddleware):
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TypeError, ValueError)

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
            spider.logger.info("in _retry retries times: %s, re-yield response.request: %s" % (retries, request.url))
            return retryreq
        else:
            request.meta["url"] = request.url
            if request.meta.get("callback") == "parse":
                spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'],
                                                   spiderid=request.meta['spiderid'],
                                                   appid=request.meta['appid'])
            self.logger.info(
                "in retry request error to failed pages url:%s, exception:%s, meta:%s" % (request.url, reason, request.meta))
            spider.crawler.stats.set_failed_download_value(request.meta, "%s_%s"%(reason, "retry many times. "))
            self.logger.debug("Gave up retrying %s (failed %d times): %s"%(request.url, retries, reason))
            raise IgnoreRequest("max retry times")
