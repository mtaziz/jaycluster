from scrapy.downloadermiddlewares.stats import DownloaderStats
from scrapy.utils.response import response_httprepr
from scrapy.conf import settings
import twisted

class CostomDownloaderStats(DownloaderStats):


    def process_response(self, request, response, spider):
        self.stats.inc_value('downloader/response_count', spider=spider)
        self.stats.inc_value('downloader/response_status_count/%s' % response.status, spider=spider)
        reslen = len(response_httprepr(response))
        self.stats.inc_value('downloader/response_bytes', reslen, spider=spider)
        request.meta["url"] = request.url
        # if response.status not in spider.crawler.settings["RETRY_HTTP_CODES"]+[301, 302, 303, 307, 200]:
        #     if request.meta.get("if_next_page"):
        #         self.stats.inc_total_pages(crawlid=request.meta['crawlid'],
        #                                            spiderid=request.meta['spiderid'],
        #                                            appid=request.meta['appid'])
        #     self.stats.set_failed_download_value(request.meta, response_status_message(response.status))
        # else:
        return response

    def process_exception(self, request, exception, spider):
        ex_class = "%s.%s" % (exception.__class__.__module__, exception.__class__.__name__)
        self.stats.inc_value('downloader/exception_count', spider=spider)
        retry_times = settings.get("PROCESSING_EXCEPTION_RETRY_TIMES", 20)
        times = request.meta.setdefault('exception_retry_times', 0)
        if times >= retry_times:
            request.meta["url"] = request.url
            if request.meta.get("if_next_page"):
                self.stats.inc_total_pages(crawlid=request.meta['crawlid'],
                                                   spiderid=request.meta['spiderid'],
                                                   appid=request.meta['appid'])
            spider._logger.info("in stats request error to failed pages url:%s, exception:%s, meta:%s"%(request.url, exception, request.meta))
            print "in stats  request error to failed pages url:%s, exception:%s, meta:%s"%(request.url, exception, request.meta)
            self.stats.set_failed_download_value(request.meta, ex_class)
            self.stats.inc_value('downloader/exception_type_count/%s' % ex_class, spider=spider)
