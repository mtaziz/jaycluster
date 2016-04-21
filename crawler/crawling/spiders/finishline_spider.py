
from scrapy import Selector
from scrapy.http import Request
from urlparse import urljoin
from jay_cluster_spider import JayClusterSpider
from crawling.items import FinishlineItem
from crawling.utils import format_html_string, parse_method_wrapper, parse_image_method_wrapper
import json
import re

class FinishlineSpider(JayClusterSpider):

    name = "finishline"

    def __init__(self, *args, **kwargs):
        super(FinishlineSpider, self).__init__(*args, **kwargs)

    @parse_method_wrapper
    def parse(self, response):
        print("FinishlineSpider#parse ...")
        self._logger.debug("FinishlineSpider#parse ...")
        item_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//div[@class="product-container"]/a/@href').extract()
            ))
        ]
        if not len(item_urls) and not response.meta.get("if_next_page"):
            self.crawler.stats.set_failed_download_value(response.meta, "this url is invalid", True)
            self.crawler.stats.set_total_pages(response.meta['crawlid'], response.meta['spiderid'],
                                               response.meta['appid'])
            return
        self.crawler.stats.inc_total_pages(response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'], len(item_urls))
        for item_url in item_urls:
            yield Request(url=item_url,
                          callback=self.parse_item,
                          meta=response.meta,
                          dont_filter=True)
        response.meta["if_next_page"] = True
        next_page_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//*[@id="searchHeaderGridWrapper"]//li[@class="next"]/../@href').extract()
            ))
        ]

        for next_page_url in next_page_urls:
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta,
                          dont_filter=True)

    @parse_image_method_wrapper
    def parse_images(self, response):
        item = response.meta['item-half']
        m = re.findall(r'"url": "(.*?)"', response.body)
        image_urls = []
        for x in m:
            image_urls.append(x)
        item['image_urls'] = image_urls
        return item

    @parse_method_wrapper
    def parse_item(self, response):
        print("FinishlineSpider#parse_item ...")
        self._logger.debug("FinishlineSpider#parse_item ...")
        sel = Selector(response)
        item = FinishlineItem()
        self._enrich_base_data(item, response, is_update=False)
        self._enrich_same_part(item, response)

        item['title'] = ''.join(sel.xpath('//h1[@id="title"]/text()').extract()).strip()
        list_size = []
        sizes = sel.xpath('//div[@id="productSizes"]/div[@class="size"]')
        for size in sizes:
            list_size.append([
                ''.join(size.xpath('@id').extract()),
                ''.join(size.xpath('text()').extract())
            ])
        item['size'] = list_size
        item['productDescription'] = format_html_string(''.join(sel.xpath('//div[@id="productDescription"]').extract()))
        item['product_images'] = json.loads(''.join(sel.re(r"JSON.parse\(\'(.*?)\'")).strip())
        item['links'] = ''.join(sel.re(r"links: \'(.*?)\'")).split(';')
        item['product_color'] = ''.join(sel.re(r'"product_color" : \["(.*?)\"'))
        item['style_color_ids'] = ''.join(sel.xpath('//div[@id="styleColors"]/span[@class="styleColorIds"]/text()').extract())

        colorid = ''.join(sel.xpath('//h1[@id="title"]/@data-colorid').extract())

        styleid = ''.join(sel.xpath('//h1[@id="title"]/@data-styleid').extract())

        imageset_url = 'http://www.finishline.com/store/api/scene7/imageset/?colorId=%s&styleId=%s' % (colorid,styleid)

        meta = response.meta
        meta['item-half'] = item
        req = Request(
                url=imageset_url,
                meta=meta,
                callback=self.parse_images,
                dont_filter=response.request.dont_filter
            )

        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )
        print('self.crawler.stats.inc_crawled_pages::::::::::',)
        yield req

    @parse_method_wrapper
    def parse_item_update(self, response):
        item = FinishlineItem()
        self._enrich_base_data(item, response, is_update=True)
        self._enrich_same_part(item, response)
        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )
        return item

    def _enrich_same_part(self, item, response):
        sel = Selector(response)
        item['nowPrice'] = ''.join(sel.xpath('//div[@id="productPrice"]/div/span[@class="nowPrice"]/text()').extract()).strip()
        item['wasPrice'] = ''.join(sel.xpath('//div[@id="productPrice"]/div/span[@class="wasPrice"]/text()').extract()).strip()
        item['price'] = sel.re(r'price: \"(.*?)\"')
        item['product_id'] = ''.join(sel.re(r'"product_id" : \["(.*?)\"'))
