from scrapy.http import Request
import os
import json
import hashlib
import socket
import fcntl
import struct
import sys
import datetime
import traceback
import pickle
from functools import wraps
from scrapy import Item
from scrapy.conf import settings
from contant import *

def validate_item_wrapper(_type):
    def process_item(func):
        @wraps(func)
        def wrapper_method(*args, **kwargs):
            try:
                self = args[0]
                response = args[1]
                item = func(*args, **kwargs)
                if isinstance(item, Item):
                    datum = dict(item)
                    validate(datum, self.name, _type)
            except RuntimeError:
                e = sys.exc_info()
                self.logger.error(traceback.format_exception(*e))
                path = dump_response_body(REGX_SPIDER_DICT[_type][self.name].search(item["meta"]["url"]).group(1), response.body)
                self.crawler.stats.inc_invalidate_property_value(item["crawlid"], item["meta"]["appid"], self.name, path, "%s:%s"%(e[0].__name__, e[1]))
            return item
        if settings.get("VALIDATE_DEBUG", False):
            return wrapper_method
        else:
            return func
    return process_item

def validate(item, name, _type):
    miss_properties = []
    for property in VALIDATE_DICT[name][_type]:
        if item.get(property, None) in (None, ""):
            miss_properties.append(property)
    if VALIDATE_FUNCTION_DICT[name](miss_properties, _type, item):
        raise RuntimeError("miss property %s"%miss_properties)

def parse_method_wrapper(func):
    @wraps(func)
    def wrapper_method(*args, **kwds):
        try:
            return func(*args, **kwds)
        except Exception:
            e = sys.exc_info()
            self = args[0]
            response = args[1]
            msg = "error heppened in %s method. Error:%s"%(func.__name__, traceback.format_exception(*e))
            self._logger.info(msg)
            self.crawler.stats.set_failed_download_value(response.meta, "%s:%s heppened in %s"%(e[0].__name__, e[1], func.__name__))
    return wrapper_method

def parse_image_method_wrapper(func):
    @wraps(func)
    def wrapper_method(*args, **kwds):
        try:
            return func(*args, **kwds)
        except Exception:
            e = sys.exc_info()
            self = args[0]
            response = args[1]
            msg = "error heppened in %s method. Error:%s"%(func.__name__, traceback.format_exception(*e))
            self._logger.info(msg)
            item = response.meta.get("item-half", {})
            self.crawler.stats.set_failed_download_images(response.meta, "%s product_Id:%s"%("%s:%s heppened in %s"%(e[0].__name__, e[1], func.__name__), item.get('product_id')))
            return item
    return wrapper_method

def next_request_method_wrapper(self):
    def wrapper(func):
        @wraps(func)
        def wrapper_method(*args, **kwds):
            try:
                return func(*args, **kwds)
            except Exception:
                e = sys.exc_info()
                msg = "error heppened in %s method. Error:%s"%(func.__name__, traceback.format_exception(*e))
                self.logger.info(msg)
                if self.present_item:
                    self.spider.crawler.stats.set_failed_download_value(self.present_item if not isinstance(self.present_item, Request) else self.present_item["meta"], "%s:%s heppened in %s"%(e[0].__name__, e[1], func.__name__))
        return wrapper_method
    return wrapper

def pipline_method_wrapper(func):
    @wraps(func)
    def wrapper_method(*args, **kwds):
        count = 0
        spider = args[2]
        item = args[1]
        while count < 3:
            try:
                return func(*args, **kwds)
            except Exception:
                e = sys.exc_info()
                spider.log("error heppened in %s method. Error:%s, processing %s,"%(func.__name__, traceback.format_exception(*e), str(item)))
                #spider.crawler.stats.set_failed_download_value(response.meta, str(e[1]))
                continue
        spider.crawler.stats.set_failed_download_value(item.meta, str(e))
        return item
    return wrapper_method

class RedisDict(dict):
    keys = None
    def __init__(self, redis_conn, crawler, primary_key=None):
        self.redis_conn = redis_conn
        self.keys = set()
        self.worker_id = primary_key if primary_key else ("%s:%s_%s:stats" % (crawler.spidercls.name, socket.gethostname(), get_raspberrypi_ip_address())).replace('.', '-')
        self.redis_conn.delete(self.worker_id)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.keys.add(key)
        self.redis_conn.hset(self.worker_id, key, pickle.dumps(value))

    def get(self, key, default=None):
        k = self.redis_conn.hget(self.worker_id, key)
        return pickle.loads(k) if k else default

    def setdefault(self, key, default=None):
        d = self.get(key, default)
        if d == default:
            self[key] = default
        return d

    def __str__(self):
        sub = "{\n"
        for key in self.keys:
            sub += "\t%s:%s, \n"%(key, self.get(key, 0))
        return sub[:-3]+"\n}"

    def set_key(self, key):
        self.worker_id = key

    def clear(self):
        self.redis_conn.delete(self.worker_id)
        self.keys.clear()

    __repr__  = __str__

def _get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def get_raspberrypi_ip_address():

    try:
        r = _get_ip_address('eth0')
    except:
        try:
            r = _get_ip_address('enp0s3')
        except:
            try:
                r = _get_ip_address('enp0s8')
            except:
                r = _get_ip_address('ens32')



    return r

def sha1(x):
    return hashlib.sha1(x).hexdigest()


def dump_response_body(name_base, response_body, path="debug"):
    '''dump response to a html file.'''
    if not os.path.exists(path):
        os.mkdir(path)
    file_name = "%s_debug_%s.html" % (name_base, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    path = os.path.abspath(os.path.join(path, file_name))
    FILE = open(path, 'w')
    FILE.writelines(response_body)
    FILE.close()
    return path


def format_html_string(a_string):
    a_string = a_string.replace('\n', '')
    a_string = a_string.replace('\t', '')
    a_string = a_string.replace('\r', '')
    a_string = a_string.replace('  ', '')
    a_string = a_string.replace(u'\u2018', "'")
    a_string = a_string.replace(u'\u2019', "'")
    a_string = a_string.replace(u'\ufeff', '')
    a_string = a_string.replace(u'\u2022', ":")
    re_ = re.compile(r"<([a-z][a-z0-9]*)\ [^>]*>", re.IGNORECASE)
    a_string = re_.sub('<\g<1>>', a_string, 0)
    re_script = re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', re.I)
    a_string = re_script.sub('', a_string)
    return a_string


def re_search(re_str, text, dotall=True):
    if dotall:
        match_obj = re.search(re_str, text, re.DOTALL)
    else:
        match_obj = re.search(re_str, text)

    if match_obj is not None:
        t = match_obj.group(1).replace('\n', '')
        t = t.replace("'", '"')
        return t
    else:
        return ""


def safely_json_loads(json_str):
    if ('' == json_str):
        return {}
    else:
        return json.loads(json_str)


def get_method(obj, name):
    name = str(name)
    try:
        return getattr(obj, name)
    except AttributeError:
        raise ValueError("Method %r not found in: %s" % (name, obj))