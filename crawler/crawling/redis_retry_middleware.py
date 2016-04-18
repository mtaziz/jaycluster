from scrapy.downloadermiddlewares.retry import RetryMiddleware
<<<<<<< HEAD
from scrapy.exceptions import IgnoreRequest
=======
>>>>>>> 2b6efcc4b238665fcb7cf1940aeee3138361a825


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
<<<<<<< HEAD
        else:
            spider.crawler.stats.set_failed_download_value(request.meta, "%s_%s"%(reason, "retry___"))
            raise IgnoreRequest("max retry times")
=======
>>>>>>> 2b6efcc4b238665fcb7cf1940aeee3138361a825
