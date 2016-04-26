# -*- coding:utf-8 -*-
import re

VALIDATE_DICT = {"amazon":{"get":['variations_data', 'parent_asin', 'product_specifications', 'product_description', 'color_images', 'variations_data', 'dimensions_display'], "update":['price', 'list_price', 'price_3p']}}

REGX_SPIDER_DICT = {"update":{
'amazon':re.compile(r'http://www.amazon.com/gp/product/(.*)/'),
'eastbay':re.compile(r'http://www.eastbay.com/product/model:(.*)/'),
'finishline':re.compile(r'http://www.finishline.com/store/catalog/product.jsp?productId=(.*)'),
'drugstore':re.compile(r'http://www.drugstore.com/products/prod.asp?pid=(.*)'),
'zappos':re.compile(r'http://www.zappos.com/product/(.*)'),
'6pm':re.compile(r'http://www.6pm.com/product/(.*)'),
'ashford':re.compile(r'http://www.ashford.com/us/(.*).pid')
}, "get":{'amazon':re.compile(r'.*/dp/(.*?)/'),}}

VALIDATE_FUNCTION_DICT = {
                            "amazon":lambda lst, _type, item:_type == "get" and lst or _type == "update" and len(lst) == 3 and item.get("availability") not in ["false"],
                          }