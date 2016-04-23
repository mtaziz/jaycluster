#coding:utf-8
from scrapy import Selector
from scrapy.http import Request
from urlparse import urljoin
from jay_cluster_spider import JayClusterSpider
from urlparse import urlparse
from crawling.items import MacysItem
from crawling.utils import format_html_string
import json
from itertools import chain
import re
import urllib2


def get_model_from_url(url):
    match_obj = re.search(r"model:(?P<model>\d+)", url)
    return match_obj.group('model')


def build_imageset_url(sku):
    '''
    图片集合: http://images.eastbay.com/is/image/EBFL/15121115?req=imageset
    (JSON)  : http://images.eastbay.com/is/image/EBFL/15121115?req=imageset,json
    '''
    return "http://images.eastbay.com/is/image/EBFL2/%s?req=imageset" % sku


def build_image_url(image_path):
    ''' http://images.eastbay.com/is/image/EBFL/15121115?wid=1000&hei=1000'''
    return "http://images.eastbay.com/is/image/%s?wid=1000&hei=1000" % image_path


def parse_imageset(imageset_str):
    return list(set(chain.from_iterable(
        (x.split(';') for x in imageset_str.split(','))
    )))


class MacysSpider(JayClusterSpider):
    name = "macys"
    have_seen_models = set()
    #start_urls = ["http://www1.macys.com/shop/mens-clothing/mens-boat-shoes?id=55636&edge=hybrid"]

    def __init__(self, *args, **kwargs):
        super(MacysSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        # self.job_status_monitor.set_init_value(response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'])
        #
        # print('job_status_monitor.set_init_value:::::::::',response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'])

        self._logger.info("MacysSpider#parse ...")
        parts = urlparse(response.url)
        url = "%s://%s/"%(parts.scheme, parts.netloc)

        item_urls = [
            urljoin(url, x) for x in list(set(
                response.xpath('//a[@class="productThumbnailLink"]/@href').extract()
            ))
        ]
        self.crawler.stats.inc_total_pages(response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'], len(item_urls))
        for item_url in item_urls:
            # model = get_model_from_url(item_url)
            # if model not in MacysSpider.have_seen_models:
            #     MacysSpider.have_seen_models.add(model)
                yield Request(url=item_url,
                              callback=self.parse_item,
                              meta=response.meta)

        next_page_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath("//a[@class='nextClass paginationSpacer']/text()")
            ))
        ]

        for next_page_url in next_page_urls:
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta)

    def get_base_urls(self, noscripts):

        return noscripts.re(r".*src=\"(http://.*?(?=\?))")

    def parse_item(self, response):
        sel = Selector(response)
        item = MacysItem()
        self._enrich_base_data(item, response, is_update=False)
        #self._enrich_same_part(item, response)
        item['title'] = ''.join(sel.xpath('//h1[@id="productTitle"]/text()').extract()).strip()
        item['description'] = sel.xpath("//div[@id='longDescription']/text()").extract()[0]+'n'+'\n'.join(sel.xpath("//ul[@id='bullets']/li/text()").extract()).strip()
        url_prefix = "/".join(response.xpath("//script[@id='pdpMainData']/text()").re(r'"imageUrl": "(.*)"')[0].split("/")[:7])
        item["image_urls"] = map(lambda x:"%s/%s%s"%(url_prefix, x, "?wid=1320&hei=1616"), sel.xpath("//script/text()").re(r"imgList: '(.*)'")[0].split(","))
        productId = sel.xpath("//input[@id='productId']/@value").extract()
        item["productId"] = productId if isinstance(productId, str) else productId[0]
        item["productTypeName"] = sel.xpath("//input[@id='productTypeName']/@value").extract()
        item["size"] = sel.xpath("//ul[@id='sizeList%s']/li/span/text()"%item["productId"]).extract()
        item["color"] = sel.xpath("//ul[@id='colorList%s']/li/img/@title"%item["productId"]).extract()
        item["sku"] = eval(sel.xpath("//script/text()").re(r'MACYS.pdp.upcmap\["%s"\] = \[(.*?)\]'%item["productId"])[0])
        # item["price"] = sel.xpath("//ul[@id='colorList%s']/li/span/text()").extract()
        # sku_images = {}
        # for sku in item.skus():
        #     url = build_imageset_url(sku)
        #     self.log("http get imageset: %s" % url)
        #     req = urllib2.Request(url)
        #     response_image = urllib2.urlopen(req)
        #     imageset_str = response_image.read()
        #     imageset = parse_imageset(imageset_str.strip())
        #     sku_images[sku] = [build_image_url(image_path) for image_path in imageset]
        #noscript_body = sel.xpath("//div[@id='imageZoomer']/text()")
        #rex = r'.*?"imageZoomer".*\r?\n<noscript>([\d\D]+?)</noscript>'
        #print >> open(item['title'], "w"), # noscript_body.extract()

        #item['image_urls'] = map(lambda x: x+"?wid=1320&hei=1616", self.get_image_urls(noscript_body))
        #item['image_urls'] = map(lambda x:x.replace("59", "330").replace("72", "404"), sel.xpath("//div[@id='altZoomerImages']/ul/li/img/@src").extract())
        #item['image_urls'] = list(chain.from_iterable(sku_images.values()))
        # self.job_status_monitor.inc_crawled_pages(
        #     crawlid=response.meta['crawlid'],
        #     spiderid=response.meta['spiderid'],
        #     appid=response.meta['appid']
        # )

        return item

    def parse_item_update(self, response):
        item = MacysItem()
        self._enrich_base_data(item, response, is_update=True)
        self._enrich_same_part(item, response)
        self.job_status_monitor.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )

        return item

    # def _enrich_same_part(self, item, response):
    #     sel = Selector(response)
    #     #item['NBR'] = ''.join(sel.re(r'var model_nbr = (.*);')).strip()
    #     #item['model'] = json.loads(''.join(sel.re(r'var model = (.*);')).strip().replace('&nbsp;', ''))
    #     item['styles'] = json.loads(''.join(sel.re(r'var styles = (.*);')).strip().replace('&nbsp;', ''))
