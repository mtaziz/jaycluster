# -*- coding:utf-8 -*-
from scrapy.downloadermiddlewares.redirect import RedirectMiddleware
from scrapy.utils.response import response_status_message
from scrapy.exceptions import IgnoreRequest

class CustomRedirectMiddleware(RedirectMiddleware):
    def __init__(self, crawler):
        super(CustomRedirectMiddleware, self).__init__(crawler.settings)
        self.stats = crawler.stats
        self.crawler = crawler

    @property
    def logger(self):
        return self.crawler.spider._logger

    def _redirect(self, redirected, request, spider, reason):
        reason = response_status_message(reason)
        ttl = request.meta.setdefault('redirect_ttl', self.max_redirect_times)
        redirects = request.meta.get('redirect_times', 0) + 1
        if spider.name == "amazon" and redirected.url[11:17] != "amazon" and redirects <= self.max_redirect_times:
            spider.logger.info("redirect to wrong url: %s" % redirected.url)
            new_request = request.copy()
            new_request.dont_filter = True
            new_request.meta["redirect_times"] = redirects
            spider.logger.info("in _redirect redirect_times: %s re-yield response.request: %s" % (redirects, request.url))
            return new_request

        if ttl and redirects <= self.max_redirect_times:
            redirected.meta['redirect_times'] = redirects
            redirected.meta['redirect_ttl'] = ttl - 1
            redirected.meta['redirect_urls'] = request.meta.get('redirect_urls', []) + \
                                               [request.url]
            redirected.dont_filter = request.dont_filter
            redirected.priority = request.priority + self.priority_adjust
            self.logger.debug("Redirecting %s to %s from %s for %s times "%(reason, redirected.url, request.url, redirected.meta.get("redirect_times")))
            return redirected
        else:
            self.logger.debug("Discarding %s: max redirections reached"%request.url)
            request.meta["url"] = request.url
            if request.meta.get("callback") == "parse":
                spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'],
                                                     spiderid=request.meta['spiderid'],
                                                     appid=request.meta['appid'])
            spider._logger.info(
                " in redicrect request error to failed pages url:%s, exception:%s, meta:%s" % (request.url, reason, request.meta))
            self.stats.set_failed_download_value(request.meta, reason)
            raise IgnoreRequest("max redirections reached")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)