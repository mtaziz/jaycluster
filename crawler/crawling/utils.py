
import re
import json
import hashlib
import socket
import fcntl
import struct
import sys
import traceback
from functools import wraps

def method_wrapper(func):
    @wraps(func)
    def wrapper_method(*args, **kwds):
        try:
            return func(*args, **kwds)
        except Exception:
            e = sys.exc_info()
            self = args[0]
            response = args[1]
            msg = "error heppened in %s method. Error:%s"%(func.__name__, traceback.format_exception(*e))
            self.log(msg)
            self.crawler.stats.set_failed_download_value(response.meta, str(e[1]))
    return wrapper_method

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
        spider.crawler.stats.set_failed_download_value(item.meta, str(e[1]))
        return item
    return wrapper_method

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


def dump_response_body(name_base, response_body):
    '''dump response to a html file.'''
    file_name = "%s_debug.html" % name_base
    FILE = open(file_name, 'w')
    FILE.writelines(response_body)
    FILE.close()


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