import socket
from redis_spider import RedisSpider
from crawling.utils import get_raspberrypi_ip_address
import time


VERSION = '2016.03.24'


class JayClusterSpider(RedisSpider):
    name = "jay_cluster_spider"

    def __init__(self, *args, **kwargs):
        super(JayClusterSpider, self).__init__(*args, **kwargs)
        self.worker_id = "%s_%s" % (socket.gethostname(), get_raspberrypi_ip_address())
        self.worker_id = self.worker_id.replace('.', '-')


    def parse(self, response):
        '''
        parse seed item list page for 2 things:
        1. item detail page request,
        2. next item list page request.
        '''
        raise NotImplementedError("Please implement parse() for your spider")

    def parse_item(self, response):
        raise NotImplementedError("Please implement parse_item() for your spider")

    def parse_item_update(self, response):
        raise NotImplementedError("Please implement parse_item_update() for your spider")

    def _enrich_base_data(self, item, response, is_update):
        meta = response.meta
        if 'workers' not in meta:
            meta['workers'] = {}
        if self.worker_id not in meta['workers']:  # workers: {worker: count}
            meta['workers'][self.worker_id] = 1
        else:
            meta['workers'][self.worker_id] += 1

        item['meta'] = {
            # populated from response.meta
            'appid': meta['appid'],
            # 'crawlid': meta['crawlid'],
            'spiderid': meta['spiderid'],
            'attrs': meta['attrs'],
            # populated from raw HTTP response
            'url': response.request.url,
            'response_url': response.url,
            'status_code': response.status,
            'status_msg': "OK",
            'headers': self.reconstruct_headers(response),
            'collection_name': "jay_%s_updates" % response.meta['spiderid'] if is_update else "jay_%ss" % response.meta['spiderid'],
            'workers': meta['workers'],
            'version': VERSION
        }

        item['crawlid'] = meta['crawlid']
        item['ts'] = time.strftime("%Y%m%d%H%M%S")



