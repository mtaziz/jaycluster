#coding:utf-8
from scrapy import Selector
from scrapy.http import Request
from urlparse import urljoin
from jay_cluster_spider import JayClusterSpider
from crawling.items import JomashopItem
from crawling.utils import format_html_string, parse_method_wrapper
import re


class JomashopSpider(JayClusterSpider):
    name = "jomashop"
    page_index = 1
    start_url = ''
    products_count_per_page = 64

    def __init__(self, *args, **kwargs):
        super(JomashopSpider, self).__init__(*args, **kwargs)

    @parse_method_wrapper
    def parse(self, response):
         # 保存start_url初始值
        if len(JomashopSpider.start_url) == 0:
            JomashopSpider.start_url = response.url

        sel = Selector(response)
        product_urls = sel.xpath('//ul[@class="products-grid"]/li//a[@class="product-image"]/@href').extract()
        product_urls = set(product_urls)
        has_more_page = not (len(product_urls) < JomashopSpider.products_count_per_page)
        self.crawler.stats.inc_total_pages(response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'], len(product_urls))

        for product_url in product_urls:
            yield Request(
                url=product_url,
                callback=self.parse_item,
                meta=response.meta,
                dont_filter=True)

        if has_more_page:
            JomashopSpider.page_index += 1
            more_page_url = "%s&p=%d" % (JomashopSpider.start_url, JomashopSpider.page_index)
            yield Request(
                url=more_page_url,
                callback=self.parse,
                meta=response.meta,
                dont_filter=True)

    @parse_method_wrapper
    def parse_item(self, response):
        self.log('JomashopSpider#parse_item...')
        item = JomashopItem()
        sel = Selector(response)
        self._enrich_base_data(item, response, is_update=False)
        self._enrich_same_part(item, response)
        item['shipping_availability'] = format_html_string(''.join(sel.xpath('//*[@id="product_addtocart_form"]//li[@class="pdp-shipping-availability"]/span/text()').extract()))
        MagicToolboxContainer_string = ''.join(sel.xpath('//div[@class="MagicToolboxContainer "]//span[@style="margin-top:8px;"]/text()').extract())
        item['image_urls'] = re.findall(r'data-href="(.*?)"', MagicToolboxContainer_string, re.MULTILINE | re.DOTALL)
        item['details'] = format_html_string(''.join(sel.xpath('//dd[@id="tab-container-details"]').extract()))
        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )

        return item

    @parse_method_wrapper
    def parse_item_update(self, response):
        self.log('JomashopSpider#parse_item_update...')
        item = JomashopItem()
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
        item['brand_name'] = format_html_string(''.join(sel.xpath('//form[@id="product_addtocart_form"]//span[@class="brand-name"]/text()').extract()))
        item['product_name'] = format_html_string(''.join(sel.xpath('//form[@id="product_addtocart_form"]//span[@class="product-name"]/text()').extract()))
        item['product_ids'] = format_html_string(''.join(sel.xpath('//form[@id="product_addtocart_form"]//span[@class="product-ids"]/text()').extract()))
        item['final_price'] = format_html_string(''.join(sel.xpath('//*[@id="product_addtocart_form"]//p[@class="final-price"]/meta[@itemprop="price"]/@content').extract()))
        item['retail_price'] = format_html_string(''.join(sel.xpath('//*[@id="product_addtocart_form"]//li[@class="pdp-retail-price"]/span/text()').extract()))
        item['savings'] = format_html_string(''.join(sel.xpath('//*[@id="product_addtocart_form"]//li[@class="pdp-savings"]/span/text()').extract()))
        item['shipping'] = format_html_string(''.join(sel.xpath('//*[@id="product_addtocart_form"]//li[@class="pdp-shipping"]/span/text()').extract()))

