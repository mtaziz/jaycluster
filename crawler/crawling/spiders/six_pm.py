__author__ = 'Administrator'
from crawling.spiders import ZapposSpider


class SixPMSpider(ZapposSpider):
    name = "6pm"

    def __init__(self, *args, **kwargs):
        super(SixPMSpider, self).__init__(*args, **kwargs)
