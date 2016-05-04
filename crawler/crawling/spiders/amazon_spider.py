from scutils.log_factory import LogFactory
from scrapy import Selector
from scrapy.http import Request
from urlparse import urljoin
from jay_cluster_spider import JayClusterSpider
from crawling.items import AmazonItem
from crawling.utils import format_html_string, safely_json_loads, re_search, dump_response_body, parse_method_wrapper, validate_item_wrapper
from itertools import chain
import re
import time
from crawling.settings import MONGODB_SERVER, MONGODB_PORT, MONGODB_DB
import pymongo



mongodb_conn = pymongo.MongoClient(MONGODB_SERVER, MONGODB_PORT)
mongodb_db = mongodb_conn[MONGODB_DB]
mongodb_collection_amazon_true_urls = mongodb_db['amazon_true_urls']


G_STRING_FREE_SHIPPING = '$0'
G_STRING_NO_SHIPPING_COST = 'no shipping cost'


def extract_shipping_cost_price_from_shipping_cost_string(shipping_cost_string):
    result = None
    if 'FREE' in shipping_cost_string:
        result = G_STRING_FREE_SHIPPING
    elif '+' in shipping_cost_string:
        # exmple: "+ $10.91 shipping"
        match_obj = re.search(r'\+(.*?) shipping', shipping_cost_string)
        if match_obj:
            result = match_obj.group(1).strip()

    return result


def enrich_color_images(item_base, hxs):
    color_images_json_string = ''.join(hxs.re(r'data\["colorImages"\]\s=\s(.*);')).strip()
    if (color_images_json_string == '{}') or (color_images_json_string == ''):
        color_images_json_string = ''.join(hxs.re(r"\'colorImages\'\:\s(\{.*\}),")).strip().replace("'", '"')

    item_base['color_images'] = color_images_json_string
    color_images = safely_json_loads(color_images_json_string)
    item_base['image_urls'] = image_urls_from(color_images)

    return item_base


def image_urls_from(color_images):
    if isinstance(color_images, dict):
        return map(get_the_largest_one_from_images, chain.from_iterable(color_images.values()))
    else:
        return map(get_the_largest_one_from_images, chain.from_iterable(color_images))


def get_the_largest_one_from_images(images):
    if 'hiRes' in images:
        if images['hiRes'] is not None:
            return images['hiRes']
        else:
            return images['large']
    else:
        return images['large']


class AmazonSpider(JayClusterSpider):

    name = "amazon"
    def __init__(self, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        self.change_proxy = None

    @parse_method_wrapper
    def parse(self, response):
        self._logger.info("start response in parse -> response type:%s"%type(response).__name__)
        item_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//div[@id="resultsCol"]//div[@class="a-row a-spacing-none"]/a[@class="a-link-normal a-text-normal"]/@href').extract()
            ))
        ]
        self.crawler.stats.inc_total_pages(response.meta['crawlid'], response.meta['spiderid'], response.meta['appid'], len(item_urls))
        for item_url in item_urls:
            yield Request(url=item_url,
                          callback=self.parse_item,
                          meta=response.meta)
        workers = response.meta.get('workers', {})
        for worker in workers.keys():
            workers[worker] = 0
        if "if_next_page" in response.meta: del response.meta["if_next_page"]
        next_page_urls = [
            urljoin(response.url, x) for x in list(set(
                response.xpath('//div[@id="pagn"]//span[@class="pagnRA"]/a/@href').extract()
            ))
        ]
        response.meta["if_next_page"] = True
        for next_page_url in next_page_urls:
            yield Request(url=next_page_url,
                          callback=self.parse,
                          meta=response.meta)

    @validate_item_wrapper("get")
    @parse_method_wrapper
    def parse_item(self, response):
        self._logger.info("start response in parse_item -> response type:%s" %type(response).__name__)
        sel = Selector(response)
        item = AmazonItem()
        self._enrich_base_data(item, response, is_update=False)
        
        node_id_re = re.compile(r'node=(?P<node_id>\w+)')
        # breadcrum
        node_id_hrefs = sel.xpath('//div[@id="wayfinding-breadcrumbs_feature_div"]//a/@href').extract()
        item['node_ids'] = [node_id_re.search(x).group('node_id') for x in node_id_hrefs if node_id_re.search(x)]
        # Look for Similar Items by Category
        similar_node_id_links = [x.xpath('a/@href').extract() for x in sel.xpath('//div[@id="browse_feature_div"]/div/p')]
        item['similar_node_ids'] = [[node_id_re.search(x).group('node_id') for x in links] for links in [links for links in similar_node_id_links]]
        item['parent_asin'] = ''.join(sel.re(r'"parent_asin":"(.*?)"')).strip()
        if len(item['parent_asin']) == 0:
            item['parent_asin'] = ''.join(sel.xpath('//form[@id="addToCart"]/input[@id="ASIN"]/@value').extract()).strip()
        item['title'] = ''.join(sel.xpath('//span[@id="productTitle"]/text()').extract()).strip()
        item['product_specifications'] = format_html_string(''.join(sel.xpath('//div[@id="technicalSpecifications_feature_div"]//table').extract()).strip())
        item['product_description'] = format_html_string(''.join(sel.xpath('//div[@id="productDescription"]//p/text()').extract()).strip())
        brand_href = ''.join(sel.xpath('//a[@id="brand"]/@href').extract()).strip()
        brand_re = re.compile(r'^/(?P<brand>.*)/b/')
        m = brand_re.search(brand_href)
        if m:
            brand = brand_re.search(brand_href).group('brand')
        else:
            brand = ''.join(sel.xpath('//a[@id="brand"]/text()').extract()).strip()
        item['brand'] = brand
        item['feature'] = format_html_string(''.join(sel.xpath('//div[@id="feature-bullets"]').extract()).strip())
        item['dimensions_display'] = safely_json_loads(format_html_string(''.join(sel.re(r'"dimensionsDisplay":(.*?]),')).strip()))
        item['variations_data'] = safely_json_loads(''.join(sel.re(r'"dimensionValuesDisplayData":(.*?]}),')).strip())
        enrich_color_images(item, sel)

        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )

        return item

    @validate_item_wrapper("update")
    @parse_method_wrapper
    def parse_item_update(self, response):
        self._logger.info("start response in parse_item_update -> response type:%s" % type(response).__name__)
        item = AmazonItem()
        meta = response.meta
        self._enrich_base_data(item, response, is_update=True)

        item['asin'] = re_search(r'product/(.*)/', response.url)
        sel = Selector(response)
        asin_divs = sel.xpath('//input[@id="ASIN"]/@value').extract()
        if len(asin_divs) > 0:
            item['parent_asin'] = ''.join(asin_divs[0]).strip()
        else:
            item['parent_asin'] = ''

        item['size'] = re_search(r'\"%s\":\[(.*?)\]' % item['asin'], ''.join(sel.re(r'"dimensionValuesDisplayData":(.*?]}),')).strip())
        item['dimensions_display'] = safely_json_loads(format_html_string(''.join(sel.re(r'"dimensionsDisplay":(.*?]),')).strip()))
        item['merchants'] = sel.xpath('//div[@id="merchant-info"]/a/text()').extract()
        item['merchant_3p'] = ''.join(sel.xpath('//div[@id="soldByThirdParty"]/b/text()').extract()).strip()
        item['price_3p'] = ''.join(sel.xpath('//div[@id="soldByThirdParty"]/span[contains(@class, "price3P")]/text()').extract()).strip()
        shipping_cost_3p_string = ''.join(sel.xpath('//div[@id="soldByThirdParty"]/span[contains(@class, "shipping3P")]/text()').extract()).strip()
        item['shipping_cost_3p'] = extract_shipping_cost_price_from_shipping_cost_string(shipping_cost_3p_string)
        item['from_price'] = ''.join(sel.xpath('//div[@id="mbc"]/div[@class="a-box"]/div/span/span[@class="a-color-price"]/text()').extract()).strip()
        availability_divs = [
            ''.join(sel.xpath('//div[@id="availability"]/span/text()').extract()),
            ''.join(sel.xpath('//span[@class="availRed"]/text()').extract()),
            ''.join(sel.xpath('//span[@class="availGreen"]/text()').extract())
            ]

        availability_str = ''.join(availability_divs).strip().lower()
        merchant_info_str = ''.join(sel.xpath('//div[@id="merchant-info"]/text()').extract()).strip().lower()
        if (
                (len(availability_divs) <= 0) or
                availability_str.startswith('only') or
                availability_str.startswith('in stock') or
                availability_str.startswith('usually')
        ):
            item['availability'] = 'true'
            item['availability_reason'] = "001: %s" % availability_str
        elif (
                merchant_info_str.startswith('ships from and sold by')
        ):
            item['availability'] = 'true'
            item['availability_reason'] = "002: %s" % merchant_info_str
        elif (
                availability_str.startswith('available from')
        ):
            item['availability'] = 'other'
            item['availability_reason'] = "003: %s" % availability_str
        elif availability_str.startswith('currently unavailable'):
            item['availability'] = 'false'
            item['availability_reason'] = "004: %s" % availability_str
        else:
            item['availability'] = 'false'
            item['availability_reason'] = '000: _'

        if item['availability'] in ['true']:
            item['list_price'] = ''.join([
                ''.join(sel.xpath('//div[@id="price"]//tr[1]/td[2]/text()').extract()).strip(),
                ''.join(sel.xpath('//span[@id="listPriceValue"]/text()').extract()).strip()
                ])

            item['price'] = ''.join([
                ''.join(sel.xpath('//span[@id="priceblock_ourprice"]/text()').extract()).strip(),
                ''.join(sel.xpath('//span[@id="priceblock_saleprice"]/text()').extract()).strip(),
                ''.join(sel.xpath('//span[@id="priceblock_dealprice"]/text()').extract()).strip(),
                ''.join(sel.xpath('//span[@id="actualPriceValue"]/b/text()').extract()).strip()
                ])

            if ((len(item['list_price']) + len(item['price'])) <= 0):
                #self.log("response body ILLEGAL: %s, %d, %d. Dumping ..." % (item['asin'], response.status, len(response.body)))
                self._logger.info("response body ILLEGAL: %s, %d, %d. Dumping ..." % (item['asin'], response.status, len(response.body)))
                dump_response_body(item['asin'], response.body)

            shipping_cost_string_ourprice = ''.join(sel.xpath('//*[@id="ourprice_shippingmessage"]/span/text()').extract()).strip()
            shipping_cost_string_saleprice = ''.join(sel.xpath('//*[@id="saleprice_shippingmessage"]/span/text()').extract()).strip()
            shipping_cost_string = shipping_cost_string_ourprice or shipping_cost_string_saleprice
            item['shipping_cost'] = extract_shipping_cost_price_from_shipping_cost_string(shipping_cost_string)
            self._logger.info("Spiderid: %s Crawlid: %s yield item in parse, asin: %s" % (response.meta['spiderid'],response.meta['crawlid'],item.get("asin", "unknow")))

            self.crawler.stats.inc_crawled_pages(
                crawlid=response.meta['crawlid'],
                spiderid=response.meta['spiderid'],
                appid=response.meta['appid']
            )
            return item
        elif item['availability'] in ['other']:
            item['price'] = ''.join([
                ''.join(sel.xpath('//*[@id="unqualifiedBuyBox"]//span[@class="a-color-price"]/text()').extract()).strip()
                ])

            new_url = ''.join(sel.xpath('//div[@id="unqualifiedBuyBox"]/div/div[1]/a/@href').extract()).strip()
            new_url = urljoin(response.url, new_url)

            meta['item_half'] = item

            req = Request(
                url=new_url,
                meta=meta,
                callback=self.parse_shipping_cost,
                dont_filter=response.request.dont_filter
            )
            self._logger.info("Spiderid: %s Crawlid: %s yield request in parse, asin: %s" % (response.meta['spiderid'],response.meta['crawlid'],req.meta.get("asin", "unknow")))
            return req
        else:
            self._logger.info("yield item in parse, asin: %s" % item.get("asin", "unknow"))
            self.crawler.stats.inc_crawled_pages(
                crawlid=response.meta['crawlid'],
                spiderid=response.meta['spiderid'],
                appid=response.meta['appid']
            )
            return item

    def parse_shipping_cost(self, response):
        item = response.meta['item_half']
        shipping_cost_string = ''.join(response.xpath('//*[@id="olpTabContent"]//p[@class="olpShippingInfo"]//span[@class="a-color-secondary"]//text()').extract()).strip()
        item['shipping_cost'] = extract_shipping_cost_price_from_shipping_cost_string(shipping_cost_string)
        self._logger.info("Spiderid: %s Crawlid: %s yield item in parse_shipping_cost, asin: %s" % (response.meta['spiderid'],response.meta['crawlid'],item.get("asin", "unknow")))

        self.crawler.stats.inc_crawled_pages(
                crawlid=response.meta['crawlid'],
                spiderid=response.meta['spiderid'],
                appid=response.meta['appid']
        )

        yield item


    def errback(self, failure):
        #self.log(">>> errback: %s" % failure)
        self._logger.info(">>> errback: %s" % failure)
        item = AmazonItem()
        if failure and failure.value and hasattr(failure.value, 'response'):
            response = failure.value.response
            if response:
                # item['asin'] = response.meta['attrs']['asin']
                item['meta'] = {
                    'url': response.request.url,
                    'status_code': response.status,
                    'ts': time.strftime("%Y%m%d%H%M%S")
                }
            else:
                self._logger.info("failure has NO response: %s" % item)
        else:
            self._logger.info("failure or failure.value is NULL, failure: %s" %failure)

        #self.log("<<< errback: %s" % item)
        self._logger.info("<<< errback: %s" % item)
        self.crawler.stats.inc_crawled_pages(
            crawlid=response.meta['crawlid'],
            spiderid=response.meta['spiderid'],
            appid=response.meta['appid']
        )

        return item
