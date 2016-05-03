# -*- coding:utf-8 -*-

from put_proxy_to_redis import ProxyRedisRepository
from twisted.web._newclient import ResponseNeverReceived, ResponseFailed, _WrapperException
from twisted.internet.error import TimeoutError, ConnectionRefusedError, ConnectError, TCPTimedOutError
from scutils.log_factory import LogFactory
from utils import get_raspberrypi_ip_address
from datetime import *

class HttpProxyMiddleware(object):
    DONT_RETRY_ERRORS = (
    _WrapperException, TCPTimedOutError, ResponseFailed, TimeoutError, ConnectionRefusedError, ResponseNeverReceived, ConnectError,
    ValueError, TypeError)

    def __init__(self, settings):
        self.settings = settings
        self.rep = ProxyRedisRepository(settings.get("REDIS_HOST"))
        self.proxy = "local"
        self.proxy_count = 0
        self.start_use_proxy_time = None

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        my_level = settings.get('SC_LOG_LEVEL', 'DEBUG')
        my_name = "%s_%s" % (crawler.spidercls.name, get_raspberrypi_ip_address())
        my_output = settings.get('SC_LOG_STDOUT', False)
        my_json = settings.get('SC_LOG_JSON', True)
        my_dir = settings.get('SC_LOG_DIR', 'logs')
        my_bytes = settings.get('SC_LOG_MAX_BYTES', '10MB')
        my_file = "%s_%s.log" % (crawler.spidercls.name, get_raspberrypi_ip_address())
        my_backups = settings.get('SC_LOG_BACKUPS', 5)

        cls.logger = LogFactory.get_instance(json=my_json,
                                             name=my_name,
                                             stdout=my_output,
                                             level=my_level,
                                             dir=my_dir,
                                             file=my_file,
                                             bytes=my_bytes,
                                             backups=my_backups)
        return cls(crawler.settings)

    def yield_new_request(self, request, spider):
        spider.change_proxy = True
        new_request = request.copy()
        new_request.dont_filter = True
        self.logger.info("re-yield response.request: %s" % request.url)
        print "re-yield response.request: %s" % request.url
        return new_request

    def process_request(self, request, spider):
        """
        将request设置为使用代理
        """
        if spider.name == "amazon":
            self.logger.info("current proxy is %s"%self.proxy)
            print  "current proxy is %s"%self.proxy
            if spider.change_proxy:
                self.start_use_proxy_time = self.start_use_proxy_time if self.start_use_proxy_time and self.proxy!="local" else datetime.now()
                if self.start_use_proxy_time < datetime.now() - timedelta(minutes=self.settings.get("SLEEP_MINUTES", 20)):
                    self.proxy = "local"
                else:
                    self.proxy = self.rep.pop()
                    if not self.proxy:
                        self.logger.info("repository is empty")
                        print "repository is empty"
                        self.proxy = "local"
                self.logger.info("change to %s. " % self.proxy)
                print "change to %s. " % self.proxy
                self.proxy_count = 0
            if self.proxy != "local":
                self.logger.info("use proxy %s to send request"%self.proxy)
                print "use proxy %s to send request"%self.proxy
                request.meta["proxy"] = self.proxy
                #request.meta["dont_redirect"] = True
                spider.change_proxy = False
            else:
                if request.meta.get("proxy"):del request.meta["proxy"]

    def process_response(self, request, response, spider):
        """
        检查response.status, 根据status是否在允许的状态码中决定是否切换到下一个proxy, 或者禁用proxy
        """
        if spider.name == "amazon":
            if "proxy" in request.meta.keys():
                self.logger.debug("The proxy is %s, the response is %s, the url is %s. " % (request.meta["proxy"], response.status, request.url))
                print "The proxy is %s, the response is %s, the url is %s. " % (request.meta["proxy"], response.status, request.url)

            else:
                self.logger.debug("Proxy is None, the response is %s, the url is %s," % (response.status, request.url))
                print("Proxy is None, the response is %s, the url is %s," % (response.status, request.url))

            # status不是正常的200而且不在spider声明的正常爬取过程中可能出现的
            # status列表中, 则认为代理无效, 切换代理
            if response.status != 200 \
               and (not hasattr(spider, "website_possible_httpstatus_list") \
                or response.status not in spider.website_possible_httpstatus_list):
                    self.logger.info("response status not in spider.website_possible_httpstatus_list")
                    print("response status not in spider.website_possible_httpstatus_list")
                    return self.yield_new_request(request, spider)
            elif response.status == 200:
                robot_checks = response.xpath('//title[@dir="ltr"]/text()').extract()
                if len(robot_checks) > 0:
                    self.logger.info("BANNED by amazon.com: %s" % request.url)
                    print "BANNED by amazon.com: %s" % request.url
                    return self.yield_new_request(request, spider)
            self.proxy_count += 1
            self.logger.debug("Proxy %s have crawled %s task. "%(self.proxy, self.proxy_count))
        return response

    def process_exception(self, request, exception, spider):
        """
        处理由于使用代理导致的连接异常
        """
        if spider.name == "amazon":
            ex_class = "%s.%s" % (exception.__class__.__module__, exception.__class__.__name__)
            spider.crawler.stats.inc_value('downloader/exception_count', spider=spider)
            times = request.meta.get("exception_retry_times", 20)
            retry_times = self.settings.get("PROCESSING_EXCEPTION_RETRY_TIMES", 20)
            if times >= retry_times:
                return
            self.logger.debug("%s %s: %s" % (request.meta.get("proxy", "local"), type(exception), exception))
            print "%s %s: %s" % (request.meta.get("proxy", "local"), type(exception), exception)
            # 只有当proxy_index>fixed_proxy-1时才进行比较, 这样能保证至少本地直连是存在的.
            new_request = request.copy()
            if isinstance(exception, self.DONT_RETRY_ERRORS) and self.proxy_count == 0:
                spider.change_proxy = True
            else:
                new_request.meta["exception_retry_times"] += 1
                new_request.meta['priority'] = new_request.meta['priority'] - 10
            new_request.dont_filter = True
            return new_request