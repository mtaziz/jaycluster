from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest


class RedisRetryMiddleware(RetryMiddleware):

    def __init__(self, settings):
        RetryMiddleware.__init__(self, settings)

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
            spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'],
                                               spiderid=request.meta['spiderid'],
                                               appid=request.meta['appid'])
            spider.crawler.stats.set_failed_download_value(request.meta, "%s_%s"%(reason, "retry___"))
            raise IgnoreRequest("max retry times")
