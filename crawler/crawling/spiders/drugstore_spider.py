<<<<<<< HEAD
from scrapy import Selector
from scrapy.http import Request
from urlparse import urljoin
from jay_cluster_spider import JayClusterSpider
from crawling.items import DrugstoreItem
from crawling.utils import format_html_string, re_search
import lxml.html
import urllib2

class DrugstoreSpider(JayClusterSpider):

    name = "drugstore"

    def __init__(self, *args, **kwargs):
        super(DrugstoreSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        self.crawler.stats.set_init_value(response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'])

        print("DrugstoreSpider#parse ...")
        self._logger.debug("DrugstoreSpider#parse ...")
        item_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//div[contains(@id,"gridView")]/div[2]/span/a[@class="oesLink"]/@href').extract()
            ))
        ]

        for item_url in item_urls:
            yield Request(url=item_url,
                          callback=self.parse_item,
                          meta=response.meta,
                          dont_filter=True)

        next_page_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//*[@id="tblbodycontent"]//a[@class="nextpage"]/@href').extract()
            ))
        ]

        for next_page_url in next_page_urls:
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta,
                          dont_filter=True)

    def parse_item(self, response):
        print("FinishlineSpider#parse_item ...")
        self._logger.debug("FinishlineSpider#parse_item ...")
        item = DrugstoreItem()
        self._enrich_base_data(item, response, is_update=False)
        self._enrich_same_part(item, response)
        sel = Selector(response)
        item['title'] = ' '.join(sel.xpath('//*[@id="divCaption"]/h1//text()').extract()).strip()
        item['product_details'] = format_html_string(''.join(sel.xpath('//*[@id="divPromosPDetail"]').extract()).strip())
        ingredients = ''.join(sel.xpath('//*[@id="TblProdForkFactsCntr"]').extract()).strip()
        if len(ingredients) == 0:
            ingredients = ''.join(sel.xpath('//*[@id="TblProdForkIngredients"]').extract()).strip()

        item['ingredients'] = format_html_string(ingredients)
        s = ''.join(sel.xpath('//*[@id="largeProdImageLink"]/a/@href').extract())
        relative_image_url = re_search(r"popUp\(\'(.*?)\'", s)
        full_image_url = urljoin(response.url, relative_image_url)

        image_urls = []
        while 1:
            request = urllib2.Request(full_image_url)
            response_image = urllib2.urlopen(request)
            image_html_str = response_image.read()
            node = lxml.html.fromstring(image_html_str)
            image_url = ''.join(node.xpath('//*[@id="productImage"]/img/@src'))
            image_urls.append(image_url)
            no_next_image = node.xpath('//img[contains(@src,"right_arrow_grey.gif") and @alt="no image"]')
            if no_next_image:
                break
            else:
                full_image_url = urljoin(
                    full_image_url,
                    ''.join(node.xpath('//img[@alt="see next image"]/../@href'))
                )
                if not full_image_url:
                    break

        item['image_urls'] = image_urls
        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )

        return item

    def parse_item_update(self, response):
        item = DrugstoreItem()
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
        item['suggested_price'] = ''.join(sel.xpath('//*[@id="divPricing"]/span[1]/s/text()').extract()).strip()
        item['our_price'] = ''.join(sel.xpath('//*[@id="productprice"]/span/text()').extract()).strip()
        item['product_id'] = ''.join(sel.re(r"dtmProductId = \'(.*?)\'")).strip()
=======
from scrapy import Selector
from scrapy.http import Request
from urlparse import urljoin
from jay_cluster_spider import JayClusterSpider
from crawling.items import DrugstoreItem
from crawling.utils import format_html_string, re_search
import lxml.html
import urllib2

class DrugstoreSpider(JayClusterSpider):

    name = "drugstore"

    def __init__(self, *args, **kwargs):
        super(DrugstoreSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        self.job_status_monitor.set_init_value(response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'])

        print("DrugstoreSpider#parse ...")
        self._logger.debug("DrugstoreSpider#parse ...")
        item_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//div[contains(@id,"gridView")]/div[2]/span/a[@class="oesLink"]/@href').extract()
            ))
        ]

        for item_url in item_urls:
            yield Request(url=item_url,
                          callback=self.parse_item,
                          meta=response.meta,
                          dont_filter=True)

        next_page_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//*[@id="tblbodycontent"]//a[@class="nextpage"]/@href').extract()
            ))
        ]

        for next_page_url in next_page_urls:
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta,
                          dont_filter=True)

    def parse_item(self, response):
        print("FinishlineSpider#parse_item ...")
        self._logger.debug("FinishlineSpider#parse_item ...")
        item = DrugstoreItem()
        self._enrich_base_data(item, response, is_update=False)
        self._enrich_same_part(item, response)
        sel = Selector(response)
        item['title'] = ' '.join(sel.xpath('//*[@id="divCaption"]/h1//text()').extract()).strip()
        item['product_details'] = format_html_string(''.join(sel.xpath('//*[@id="divPromosPDetail"]').extract()).strip())
        ingredients = ''.join(sel.xpath('//*[@id="TblProdForkFactsCntr"]').extract()).strip()
        if len(ingredients) == 0:
            ingredients = ''.join(sel.xpath('//*[@id="TblProdForkIngredients"]').extract()).strip()

        item['ingredients'] = format_html_string(ingredients)
        s = ''.join(sel.xpath('//*[@id="largeProdImageLink"]/a/@href').extract())
        relative_image_url = re_search(r"popUp\(\'(.*?)\'", s)
        full_image_url = urljoin(response.url, relative_image_url)

        image_urls = []
        while 1:
            request = urllib2.Request(full_image_url)
            response_image = urllib2.urlopen(request)
            image_html_str = response_image.read()
            node = lxml.html.fromstring(image_html_str)
            image_url = ''.join(node.xpath('//*[@id="productImage"]/img/@src'))
            image_urls.append(image_url)
            no_next_image = node.xpath('//img[contains(@src,"right_arrow_grey.gif") and @alt="no image"]')
            if no_next_image:
                break
            else:
                full_image_url = urljoin(
                    full_image_url,
                    ''.join(node.xpath('//img[@alt="see next image"]/../@href'))
                )
                if not full_image_url:
                    break

        item['image_urls'] = image_urls
        self.job_status_monitor.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )

        return item

    def parse_item_update(self, response):
        item = DrugstoreItem()
        self._enrich_base_data(item, response, is_update=True)
        self._enrich_same_part(item, response)
        self.job_status_monitor.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )

        return item

    def _enrich_same_part(self, item, response):
        sel = Selector(response)
        item['suggested_price'] = ''.join(sel.xpath('//*[@id="divPricing"]/span[1]/s/text()').extract()).strip()
        item['our_price'] = ''.join(sel.xpath('//*[@id="productprice"]/span/text()').extract()).strip()
        item['product_id'] = ''.join(sel.re(r"dtmProductId = \'(.*?)\'")).strip()
>>>>>>> 2b6efcc4b238665fcb7cf1940aeee3138361a825
