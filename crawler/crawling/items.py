# -*- coding: utf-8 -*-

# Define here the models for your scraped items

from scrapy import Item, Field


class RawResponseItem(Item):
    meta = Field()
    workers = Field()
    image_urls = Field()
    images = Field()
    collection_name = Field()

    appid = Field()
    crawlid = Field()
    url = Field()
    ts = Field()
    response_url = Field()
    status_code = Field()
    status_msg = Field()
    response_headers = Field()
    request_headers = Field()
    body = Field()
    links = Field()
    attrs = Field()
    success = Field()
    exception = Field()

class AmazonItem(RawResponseItem):
    parent_asin = Field()         # 父级ASIN
    node_ids = Field()            # browse nodes array, from breadcrumb navigation
    similar_node_ids = Field()    # Similar Items by Category: [node_ids]
    brand = Field()               # 品牌

    title = Field()               # 标题
    feature = Field()             #
    dimensions_display = Field()
    variations_data = Field()
    color_images = Field()        # json string
    color_images_init = Field()   # json string
    # ASIN = Field()
    product_description = Field() # 产品详细描述
    product_specifications = Field()
    images_data = Field()         # 图片的原始数据(JSON格式)

    def has_variants(self):
        return (0 < len(self["variations_data"]))

    def node_id():
        if(len(node_ids) > 0):
            return node_ids[-1]
        else:
            return None

    roc_id = Field()            # ROC_ID
    http_code = Field()         # the status code for the http response
    broken_reason = Field()     # may be banned by the remote, banned


    asin = Field()              # ASIN
    availability = Field()      # true, false, other
    availability_reason = Field()  # 对availability进行判断依据的原因

    list_price = Field()        # 原价
    price = Field()             # 现价, our price or sale price
    from_price = Field()        # other sellers on Amazon from ...
    shipping_cost = Field()     # 运费
    merchants = Field()         # 卖家列表

    merchant_3p = Field()       # 3rd party
    price_3p = Field()          # 3rd party price
    shipping_cost_3p = Field()  # 3rd party shipping cost

    size = Field()


    ts = Field()                # timestamp



class FinishlineItem(RawResponseItem):
    title = Field()
    nowPrice = Field()
    wasPrice = Field()
    size = Field()
    productDescription = Field()
    product_images = Field()
    links = Field()
    price = Field()
    product_id = Field()
    product_color = Field()
    style_color_ids = Field()


class EastbayItem(RawResponseItem):
    NBR = Field()                 # parent
    title = Field()               # 标题
    description = Field()         # 详细描述
    model = Field()               # model
    styles = Field()              # styles
    sku_images = Field()          # {sku: [image_urls], sku: [image_urls]}
    ts = Field()                  # Timestamp

    def skus(self):
        return self['model']['ALLSKUS']

class ZapposItem(RawResponseItem):
    title = Field()
    productId = Field()
    productDescription = Field()
    stockJSON = Field()
    dimensions = Field()
    dimToUnitToValJSON = Field()
    dimensionIdToNameJson = Field()
    valueIdToNameJSON = Field()
    colorNames = Field()
    colorPrices = Field()
    styleIds = Field()
    colorIds = Field()
    color_images = Field()


class AshfordItem(RawResponseItem):
    prodID = Field()
    prodName = Field()
    prod_desc = Field()
    Retail = Field()
    Ashford_price = Field()
    Save = Field()
    Weekly_Sale = Field()
    detail = Field()
    chinese_detail = Field()
    Brand = Field()
    product_images = Field()
    Your_price = Field()


class JacobtimeItem(RawResponseItem):
    brand = Field()
    descript_title = Field()
    products_id = Field()
    retail = Field()
    your_price = Field()
    details = Field()


class JomashopItem(RawResponseItem):
    brand_name = Field()
    product_name = Field()
    product_ids = Field()
    final_price = Field()
    retail_price = Field()
    savings = Field()
    shipping = Field()
    shipping_availability = Field()
    details = Field()


class DrugstoreItem(RawResponseItem):
    title = Field()
    suggested_price = Field()
    our_price = Field()
    product_details = Field()
    product_id = Field()
    ingredients = Field()

class MacysItem(RawResponseItem):

    title = Field()               # 标题
    description = Field()         # 详细描述
    productId = Field()           # productId
    productTypeName = Field()     # productTypeName

    ts = Field()                  # Timestamp
    size = Field()
    image_urls = Field()
    sku = Field()
    color = Field()
    price = Field()
