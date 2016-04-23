
#coding:utf-8
from scrapy import Selector
from scrapy.http import Request
from urlparse import urljoin
from jay_cluster_spider import JayClusterSpider
from crawling.items import AshfordItem
from crawling.utils import format_html_string, parse_method_wrapper


class AshfordSpider(JayClusterSpider):
    name = "ashford"
    seen_products = set()

    def __init__(self, *args, **kwargs):
        super(AshfordSpider, self).__init__(*args, **kwargs)

    @parse_method_wrapper
    def parse(self, response):
        item_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//div[@id="grid-4-col"]/div/div[2]/div/div/div/a[1]/@href').extract()
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
                response.xpath('//*[@id="bottomPager"]/li[@class="nextLink"]/a/@href').extract()
            ))
        ]

        for next_page_url in next_page_urls:
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta,
                          dont_filter=True)

    @parse_method_wrapper
    def parse_item(self, response):
        #self.log('AshfordSpider#parse_item...')
        self._logger.info('AshfordSpider#parse_item...')
        item = AshfordItem()
        sel = Selector(response)
        self._enrich_base_data(item, response, is_update=False)
        self._enrich_same_part(item, response)
        item['prodName'] = ''.join(sel.xpath(' //*[@id="prodName"]/a/text()').extract()).strip()
        item['prod_desc'] = (''.join(sel.xpath('//*[@id="fstCont"]/h3/text()').extract()).strip())
        item['detail'] = format_html_string(''.join(sel.xpath('//div[@id="tab1_info"]').extract()).strip())
        item['Brand'] = ''.join(sel.xpath('//h1[@id="prodName"]/a[@id="sameBrandProduct"]/text()[1]').extract()).strip()
        item['product_images'] = list(set(sel.xpath('//a[contains(@href,"/images/catalog/") and contains(@href,"XA.jpg")]/@href').extract()))
        item['image_urls'] = [urljoin(response.url, i) for i in item['product_images']]
        chinese_url = response.url.replace('www.', 'zh.')

        response.meta['item_half'] = item
        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )

        yield Request(
            url=chinese_url,
            meta=response.meta,
            callback=self.parse_chinese_detail,
            dont_filter=True
            )

    def parse_chinese_detail(self, response):
        #self.log('AshfordSpider#parse_chinese_detail...')
        self._logger.info('AshfordSpider#parse_chinese_detail...')
        sel = Selector(response)
        item = response.meta['item_half']
        item['chinese_detail'] = format_html_string(''.join(sel.xpath('//div[@id="tab1_info"]').extract()).strip())
        return item

    @parse_method_wrapper
    def parse_item_update(self, response):
        #self.log('AshfordSpider#parse_item_update...')
        self._logger.info('AshfordSpider#parse_item_update...')
        item = AshfordItem()
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
        item['prodID'] = ''.join(sel.xpath('//*[@id="prodID"]/text()').extract()).strip()
        item['Retail'] = ''.join(sel.xpath('//*[@id="pricing"]/tbody/tr[contains(th,"Retail")]/td/text()').extract()).strip()
        item['Ashford_price'] = ''.join(sel.xpath('//*[@id="pricing"]/tbody/tr[contains(th,"Ashford")]/td/text()').extract()).strip()
        item['Save'] = ''.join(sel.xpath('//*[@id="pricing"]/tbody/tr[contains(th,"Save")]/td/text()').extract()).strip()
        item['Weekly_Sale'] = ''.join(sel.xpath('//*[@id="pricing"]/tbody/tr[contains(th,"Weekly")]/td/text()').extract()).strip()
        item['Your_price'] = ''.join(sel.xpath('//*[@id="pricing"]/tbody/tr[contains(th,"Your")]/td/text()').extract()).strip()
