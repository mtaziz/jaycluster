# -*-coding:utf-8-*-
"""
Scrapy Middleware to set a random User-Agent for every Request.
Downloader Middleware which uses a file containing a list of
user-agents and sets a random one for each request.
"""

import random, re, base64
from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
import logging



class RandomProxyMiddleware(object):
    '''
    https://github.com/aivarsk/scrapy-proxies
    '''
    logger = logging.getLogger('RandomProxyMiddleware')

    def __init__(self, settings):
        self.proxy_list = settings.get('PROXY_LIST')

        self.proxies = {}
        for line in self.proxy_list.split('\n'):
            parts = re.match('(\w+://)(\w+:\w+@)?(.+)', line)

            # Cut trailing @
            if parts.group(2):
                user_pass = parts.group(2)[:-1]
            else:
                user_pass = ''

            self.proxies[parts.group(1) + parts.group(3)] = user_pass

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        # Don't overwrite with a random one (server-side state for IP)
        if 'proxy' in request.meta:
            return

        proxy_address = random.choice(self.proxies.keys())
        proxy_user_pass = self.proxies[proxy_address]

        request.meta['proxy'] = proxy_address
        self.logger.debug('proxy: {} {}'.format(proxy_address, request))
        if proxy_user_pass:
            basic_auth = 'Basic ' + base64.encodestring(proxy_user_pass)
            request.headers['Proxy-Authorization'] = basic_auth

    def process_exception(self, request, exception, spider):
        proxy = request.meta['proxy']
        self.logger.info('Removing failed proxy <%s>, %d proxies left' % (
                    proxy, len(self.proxies)))
        try:
            del self.proxies[proxy]
        except ValueError:
            pass


class RandomUserAgentMiddleware(UserAgentMiddleware):
    logger = logging.getLogger('RandomUserAgentMiddleware')

    def __init__(self, settings, user_agent='Scrapy'):
        super(RandomUserAgentMiddleware, self).__init__()
        self.user_agent = user_agent
        user_agent_list = settings.get('USER_AGENT_LIST')
        if not user_agent_list:
            # If USER_AGENT_LIST_FILE settings is not set,
            # Use the default USER_AGENT or whatever was
            # passed to the middleware.
            ua = settings.get('USER_AGENT', user_agent)
            self.user_agent_list = [ua]
        else:
            self.user_agent_list = filter(lambda x: len(x)>0, [line.strip() for line in user_agent_list.split('\n')])
        # add by msc
        self.default_agent = user_agent
        self.chicer = self.choice()
        self.user_agent = self.chicer.next() or user_agent
        self.banned_pages = 0

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls(crawler.settings)
        crawler.signals.connect(obj.spider_opened,
                                signal=signals.spider_opened)
        return obj

    # add by msc
    def choice(self):
        while True:
            if self.user_agent_list:
                for user_agent in self.user_agent_list:
                    yield  user_agent
            else:
                yield None


    def process_request(self, request, spider):
        #user_agent = random.choice(self.user_agent_list)
        # add by msc
        new_banned_pages = int(spider.redis_conn.hget("crawlid:%s:workerid:%s"%(request.meta["crawlid"], spider.worker_id), "banned_pages")  or 0)
        if new_banned_pages > self.banned_pages:
            self.banned_pages = new_banned_pages
            self.user_agent = self.chicer.next() or self.default_agent
        if self.user_agent:
            request.headers.setdefault('User-Agent', self.user_agent)
            self.logger.debug('User-Agent: {} {}'.format(request.headers.get('User-Agent'), request))
        else:
            self.logger.error('User-Agent: ERROR with user agent list')


class HttpProxySettingsMiddleware(object):
    logger = logging.getLogger('HttpProxySettingsMiddleware')

    def __init__(self, settings):
        self.proxy_address = settings.get('PROXY_ADDRESS', 'http://127.0.0.1:8080')

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls(crawler.settings)
        return obj

    # overwrite process request
    def process_request(self, request, spider):
        request.meta['proxy'] = self.proxy_address
        self.logger.debug('proxy: {} {}'.format(self.proxy_address, request))


# Start your middleware class
class ProxyMiddleware(object):
    # overwrite process request
    def process_request(self, request, spider):
        # Set the location of the proxy
        if spider.name in ["nordstrom"]:

            print ('in ProxyMiddleware ..............................')

            request.meta['proxy'] = "http://58.96.182.136:8818"
            # Use the following lines if your proxy requires authentication
            proxy_user_pass = ""
            # setup basic authentication for the proxy
            encoded_user_pass = base64.encodestring(proxy_user_pass)
            request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass