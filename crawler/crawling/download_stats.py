from scrapy.downloadermiddlewares.stats import DownloaderStats
from scrapy.utils.response import response_httprepr
from scrapy.utils.response import response_status_message

class CostomDownloaderStats(DownloaderStats):


    def process_response(self, request, response, spider):
        self.stats.inc_value('downloader/response_count', spider=spider)
        self.stats.inc_value('downloader/response_status_count/%s' % response.status, spider=spider)
        reslen = len(response_httprepr(response))
        self.stats.inc_value('downloader/response_bytes', reslen, spider=spider)
        if response.status not in spider.crawler.settings["RETRY_HTTP_CODES"]+[301, 302, 303, 307, 200]:
            self.stats.inc_total_pages(crawlid=request.meta['crawlid'],
                                               spiderid=request.meta['spiderid'],
                                               appid=request.meta['appid'])
            self.stats.set_failed_download_value(request.meta, response_status_message(response.status))
        return response

    def process_exception(self, request, exception, spider):
        ex_class = "%s.%s" % (exception.__class__.__module__, exception.__class__.__name__)
        self.stats.inc_value('downloader/exception_count', spider=spider)
        self.stats.inc_total_pages(crawlid=request.meta['crawlid'],
                                           spiderid=request.meta['spiderid'],
                                           appid=request.meta['appid'])
        self.stats.set_failed_download_value(request.meta, ex_class)
        self.stats.inc_value('downloader/exception_type_count/%s' % ex_class, spider=spider)
