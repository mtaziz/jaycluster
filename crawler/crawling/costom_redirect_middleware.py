# -*- coding:utf-8 -*-
import logging
from scrapy.downloadermiddlewares.redirect import RedirectMiddleware
from scrapy.utils.response import response_status_message
from scrapy.exceptions import IgnoreRequest
logger = logging.getLogger(__name__)

class CustomRedirectMiddleware(RedirectMiddleware):
    def __init__(self, crawler):
        super(CustomRedirectMiddleware, self).__init__(crawler.settings)
        self.stats = crawler.stats

    def _redirect(self, redirected, request, spider, reason):
        reason = response_status_message(reason)
        ttl = request.meta.setdefault('redirect_ttl', self.max_redirect_times)
        redirects = request.meta.get('redirect_times', 0) + 1

        if ttl and redirects <= self.max_redirect_times:
            redirected.meta['redirect_times'] = redirects
            redirected.meta['redirect_ttl'] = ttl - 1
            redirected.meta['redirect_urls'] = request.meta.get('redirect_urls', []) + \
                                               [request.url]
            redirected.dont_filter = request.dont_filter
            redirected.priority = request.priority + self.priority_adjust
            logger.debug("Redirecting (%(reason)s) to %(redirected)s from %(request)s",
                         {'reason': reason, 'redirected': redirected, 'request': request},
                         extra={'spider': spider})
            return redirected
        else:
            logger.debug("Discarding %(request)s: max redirections reached",
                         {'request': request}, extra={'spider': spider})
            self.stats.set_failed_download_value(request.meta, reason)
            raise IgnoreRequest("max redirections reached")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)