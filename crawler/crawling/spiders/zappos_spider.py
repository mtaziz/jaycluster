#coding:utf-8
from scrapy import Selector
from scrapy.http import Request
from urlparse import urljoin
from jay_cluster_spider import JayClusterSpider
from crawling.items import ZapposItem
from crawling.utils import format_html_string
import json
from itertools import chain
import re
import urllib2
from crawling.utils import re_search


class ZapposSpider(JayClusterSpider):
    name = "zappos"
    seen_products = set()

    def __init__(self, *args, **kwargs):
        super(ZapposSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        item_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//*[@id="searchResults"]/a/@href').extract()
            ))
        ]
        self.crawler.stats.inc_total_pages(response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'], len(item_urls))
        for item_url in item_urls:
            yield Request(url=item_url,
                          callback=self.parse_item,
                          meta=response.meta)

        next_page_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//*[@id="resultWrap"]//div[@class="pagination"]/a[contains(text(),"»")]/@href').extract()
            ))
        ]

        for next_page_url in next_page_urls:
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta)

    def parse_item(self, response):
        sel = Selector(response)
        item = ZapposItem()
        self._enrich_base_data(item, response, is_update=False)
        item['productId'] = ''.join(sel.xpath('//form[@id="prForm"]/input[@name="productId"]/@value').extract()).strip()

        if item['productId'] in self.seen_products:
            return
        else:
            self.seen_products.add(item['productId'])
        self._enrich_same_part(item, response)
        positions = ['p', '1', '2', '3', '4', '5', '6']
        all_images = []
        image_urls = []
        for one_colorId in item['colorIds']:
            for one_position in positions:
                reg_str = r"pImgs\[%s\]\[\'4x\'\]\[\'%s\'\] = . filename: '(.*?)'," % (one_colorId, one_position)
                image_file = re_search(reg_str, response.body, dotall=False)
                image_file.replace("'", "")
                image_file.replace('"', "")
                all_images.append([one_colorId, one_position, image_file])
                if len(image_file) > 0:
                    image_urls.append(image_file)

        item['color_images'] = all_images
        item['image_urls'] = image_urls
        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )
        print('item====', item)
        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )

        return item

    def parse_item_update(self, response):
        item = ZapposItem()
        self._enrich_base_data(item, response, is_update=True)
        self._enrich_same_part(item, response)
        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )
        print('item====', item)
        return item

    def _enrich_same_part(self, item, response):
        sel = Selector(response)
        item['title'] = ' '.join(sel.xpath('//*[@id="prdImage"]/h1/*//text()').extract()).strip()
        if len(item['title']) < 2:
            item['title'] = ' '.join(sel.xpath('//*[@id="productStage"]/h1/*/text()').extract()).strip()

        item['productDescription'] = format_html_string(''.join(sel.xpath('//div[@id="prdInfoText"]').extract()).strip())
        if len(item['productDescription']) == 0:
            item['productDescription'] = format_html_string(''.join(sel.xpath('//div[@id="productDescription"]').extract()).strip())

        item['stockJSON'] = json.loads(''.join(sel.re(r'var stockJSON =(.*);')).strip().replace('&nbsp;', ''))
        item['dimensions'] = json.loads(''.join(sel.re(r'var dimensions =(.*);')).strip().replace('&nbsp;', ''))
        item['dimToUnitToValJSON'] = json.loads(''.join(sel.re(r'var dimToUnitToValJSON =(.*);')).strip().replace('&nbsp;', ''))
        item['dimensionIdToNameJson'] = json.loads(''.join(sel.re(r'var dimensionIdToNameJson =(.*);')).strip().replace('&nbsp;', ''))
        item['valueIdToNameJSON'] = json.loads(''.join(sel.re(r'var valueIdToNameJSON =(.*);')).strip().replace('&nbsp;', ''))
        item['colorNames'] = json.loads(re_search(r'var colorNames =(.*?);', response.body))
        item['colorPrices'] = json.loads(re_search(r'var colorPrices =(.*?);', response.body))
        item['styleIds'] = json.loads(re_search(r'var styleIds =(.*?);', response.body))
        item['colorIds'] = json.loads(re_search(r'var colorIds =(.*?);', response.body))