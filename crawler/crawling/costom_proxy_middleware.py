# -*- coding:utf-8 -*-
from scrapy.exceptions import IgnoreRequest
from put_proxy_to_redis import ProxyRedisRepository
from twisted.web._newclient import ResponseNeverReceived, ResponseFailed, _WrapperException
from twisted.internet.error import TimeoutError, ConnectionRefusedError, ConnectError, TCPTimedOutError
from custom_log_factory import CustomLogFactory
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
        self.proxy_useful = 0
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

        cls.logger = CustomLogFactory.get_instance(json=my_json,
                                             name=my_name,
                                             stdout=my_output,
                                             level=my_level,
                                             dir=my_dir,
                                             file=my_file,
                                             bytes=my_bytes,
                                             backups=my_backups)
        cls.crawler = crawler
        return cls(crawler.settings)

    def yield_new_request(self, request, spider):
        if self.proxy_useful < 1:
            spider.change_proxy = True
            new_request = request.copy()
            new_request.dont_filter = True
            self.logger.info("re-yield response.request: %s" % request.url)
            return new_request
        else:
            self.proxy_useful /= 2


    def process_request(self, request, spider):
        """
        将request设置为使用代理
        """
        if spider.name == "amazon":
            self.logger.info("current proxy is %s"%self.proxy)
            if spider.change_proxy:
                self.start_use_proxy_time = self.start_use_proxy_time if self.start_use_proxy_time and self.proxy!="local" else datetime.now()
                if self.start_use_proxy_time < datetime.now() - timedelta(minutes=self.settings.get("SLEEP_MINUTES", 20)):
                    self.proxy = "local"
                else:
                    self.proxy = self.rep.pop()
                    if not self.proxy:
                        self.logger.info("repository is empty")
                        self.proxy = "local"
                self.logger.info("change to %s. " % self.proxy)
                self.proxy_count = 0
                self.proxy_useful = 0
            if self.proxy != "local":
                self.logger.info("use proxy %s to send request"%self.proxy)
                request.meta["proxy"] = self.proxy
                #request.meta["dont_redirect"] = True  # 有些代理会把请求重定向到一个莫名其妙的地址
                spider.change_proxy = False
            else:
                if request.meta.get("proxy"):del request.meta["proxy"]

    def process_response(self, request, response, spider):
        """
        检查response.status, 根据status是否在允许的状态码中决定是否切换到下一个proxy, 或者禁用proxy
        """
        if spider.name == "amazon":
            if "proxy" in request.meta.keys():
                self.logger.info("The proxy is %s, the response is %s, the url is %s. " % (request.meta["proxy"], response.status, request.url))
            else:
                self.logger.info("Proxy is None, the response is %s, the url is %s," % (response.status, request.url))
            # status不是正常的200而且不在spider声明的正常爬取过程中可能出现的
            # status列表中, 则认为代理无效, 切换代理
            if response.status != 200 \
               and (not hasattr(spider, "website_possible_httpstatus_list") \
                or response.status not in spider.website_possible_httpstatus_list):
                    self.logger.info("response status not in spider.website_possible_httpstatus_list")
                    return self.yield_new_request(request, spider) or response
            elif response.status == 200:
                robot_checks = response.xpath('//title[@dir="ltr"]/text()').extract()
                if len(robot_checks) > 0:
                    self.logger.info("BANNED by %s: %s" % (request.meta.get("proxy", "local"), request.url))
                    if request.meta.setdefault('workers', {}).setdefault(spider.worker_id,
                                                                          0) >= self.settings.get(
                            "BANNED_RETRY_TIMES", 3):
                        if request.meta.get("callback") == "parse":
                            spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'],
                                                                 spiderid=request.meta['spiderid'],
                                                                 appid=request.meta['appid'])
                            page_type = "if_next_page" if request.meta.get("if_next_page") else "index_page"
                        else:
                            page_type = "update_page" if request.meta.get("callback") == "parse_item_update" else "get_page"
                        self.crawler.stats.inc_drop_pages(
                            crawlid=request.meta['crawlid'],
                            spiderid=request.meta['spiderid'],
                            appid=request.meta['appid'],
                            url=request.url,
                            worker_id=spider.worker_id,
                            page_type=page_type
                        )

                        self.logger.info("drop request url: %s" % request.url)
                        raise IgnoreRequest("max bans reached")
                    else:
                        request.meta.get('workers')[spider.worker_id] += 1
                        return self.yield_new_request(request, spider) or response
            elif response.url[11:17] != "amazon":
                self.logger.info("redirect to wrong url: %s" % response.url)
                return self.yield_new_request(request, spider)
            self.proxy_count += 1
            self.proxy_useful += 1
            self.logger.info("Proxy %s have crawled %s task. "%(self.proxy, self.proxy_count))
        return response

    def process_exception(self, request, exception, spider):
        """
        处理由于使用代理导致的连接异常
        """
        if spider.name == "amazon":
            self.logger.info("%s %s: %s" % (request.meta.get("proxy", "local"), type(exception), exception))
            if request.url[11:17] == "amazon":
                return self.yield_new_request(request, spider)
            else:
                raise IgnoreRequest("wrong domain")