
#coding:utf-8
from scrapy import Selector
from scrapy.http import Request
from urlparse import urljoin
from jay_cluster_spider import JayClusterSpider
from crawling.items import EastbayItem
from crawling.utils import format_html_string, parse_method_wrapper
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


class EastbaySpider(JayClusterSpider):
    name = "eastbay"
    have_seen_models = set()

    def __init__(self, *args, **kwargs):
        super(EastbaySpider, self).__init__(*args, **kwargs)

    @parse_method_wrapper
    def parse(self, response):
        #total_pages=None the porpose is not to init total_page add my msc
        #self.log("EastbaySpider#parse ...")
        self._logger.info("EastbaySpider#parse ...")
        item_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//*[@id="endeca_search_results"]/ul/li/a[1]/@href').extract()
            ))
        ]
        if not len(item_urls) and not response.meta.get("if_next_page"):
            self.crawler.stats.set_failed_download_value(response.meta, "this url is invalid", True)
            self.crawler.stats.set_total_pages(response.meta['crawlid'], response.meta['spiderid'],
                                               response.meta['appid'])
            return

        for item_url in item_urls:
            model = get_model_from_url(item_url)

            if model not in EastbaySpider.have_seen_models:
                self.crawler.stats.inc_total_pages(response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'])
                EastbaySpider.have_seen_models.add(model)
                yield Request(url=item_url,
                              callback=self.parse_item,
                              meta=response.meta)
        response.meta["if_next_page"] = True
        next_page_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//*[@id="endecaResultsWrapper"]/div[4]/div/div[3]/a[@class="next"]/@href').extract()
            ))
        ]

        for next_page_url in next_page_urls:
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta)
    @parse_method_wrapper
    def parse_item(self, response):
        sel = Selector(response)
        item = EastbayItem()
        self._enrich_base_data(item, response, is_update=False)
        self._enrich_same_part(item, response)
        item['title'] = ''.join(sel.xpath('//*[@id="model_name"]/text()').extract()).strip()
        item['description'] = ''.join(sel.xpath("//meta[@name='description']/@content").extract()).strip()

        sku_images = {}
        for sku in item.skus():
            url = build_imageset_url(sku)
            #self.log("http get imageset: %s" % url)
            self._logger.info("http get imageset: %s" % url)
            req = urllib2.Request(url)
            try:
                response_image = urllib2.urlopen(req)
            except urllib2.HTTPError,e:
                sku_images = "The server couldn't fulfill the request.'Error code: %s " %  e.code
            except urllib2.URLError,e:
                sku_images = "failed to reach a server. Reason: %s " % e.reason
            else:
                imageset_str = response_image.read()
                imageset = parse_imageset(imageset_str.strip())
              
                sku_images[sku] = [build_image_url(image_path) if (len(image_path) > 0) else 'no image' for image_path in imageset]

        item['sku_images'] = sku_images
        item['image_urls'] = list(chain.from_iterable(sku_images.values()))
   

        return item

    @parse_method_wrapper
    def parse_item_update(self, response):
        item = EastbayItem()
        self._enrich_base_data(item, response, is_update=True)
        self._enrich_same_part(item, response)
  

        return item

    def _enrich_same_part(self, item, response):
        sel = Selector(response)
        item['NBR'] = ''.join(sel.re(r'var model_nbr = (.*);')).strip()
        item['model'] = json.loads(''.join(sel.re(r'var model = (.*);')).strip().replace('&nbsp;', ''))
        item['styles'] = json.loads(''.join(sel.re(r'var styles = (.*);')).strip().replace('&nbsp;', ''))
        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid'])