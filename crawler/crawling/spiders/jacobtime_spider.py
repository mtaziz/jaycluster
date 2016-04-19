#coding:utf-8
from scrapy import Selector
from scrapy.http import Request
from urlparse import urljoin
from jay_cluster_spider import JayClusterSpider
from crawling.items import JacobtimeItem
from crawling.utils import format_html_string


class JacobtimeSpider(JayClusterSpider):
    name = "jacobtime"


    def __init__(self, *args, **kwargs):
        super(JacobtimeSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        self.log('JacobtimeSpider#parse.........')
        item_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//*[@id="content"]//div[@class="product-list"]/div/div[@class="link-block"]/a[2]/@href').extract()
            ))
        ]
        self.crawler.stats.inc_total_pages(response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'], len(item_urls))
        for item_url in item_urls:
            yield Request(url=item_url,
                          callback=self.parse_item,
                          meta=response.meta,
                          dont_filter=True)

        next_page_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//a[@title=" Next Page "]/@href').extract()
            ))
        ]

        for next_page_url in next_page_urls:
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta,
                          dont_filter=True)

    def parse_item(self, response):
        self.log('JacobtimeSpider#parse_item...')
        item = JacobtimeItem()
        sel = Selector(response)
        self._enrich_base_data(item, response, is_update=False)
        self._enrich_same_part(item, response)
        item['details'] = format_html_string(''.join(sel.xpath('//div[@id="tab1"]').extract()))
        item['image_urls'] = [urljoin(response.url, i) for i in sel.xpath('//a[@class="lightbox"]/@href').extract()]
        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )

        return item

    def parse_item_update(self, response):
        self.log('JacobtimeSpider#parse_item_update...')
        item = JacobtimeItem()
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
        item['brand'] = ''.join(sel.xpath('//h1/text()').extract())
        item['descript_title'] = ''.join(sel.xpath('//span[@class="descript-title"]/text()').extract())
        item['products_id'] = ''.join(sel.xpath('//span[@class="code"]/text()').extract())
        # item['retail'] = ''.join(sel.xpath('//dl[@class="descript-price"]//dt[1]/following-sibling::*[1]/text()').extract())
        item['retail'] = ''.join(sel.xpath('//ul[@class="sale-list"]/li[contains(text(),"Retail")]/text()').extract())
        # item['your_price'] = ''.join(sel.xpath('//dl[@class="descript-price"]//dd[2]/span[@class="productSpecialPriceLarge"]/text() | //dl[@class="descript-price"]//dd[2]/text()').extract())
        item['your_price'] = ''.join(sel.xpath('//span[@class="price"]/text()').extract())
