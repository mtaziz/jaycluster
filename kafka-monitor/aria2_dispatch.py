import json
import sys
import traceback
import time
import datetime
import importlib
import uuid
from docopt import docopt
from kafka import KafkaClient, SimpleConsumer, SimpleProducer
from os.path import splitext, basename, exists
from urlparse import urlparse
import hashlib
from websocket import create_connection
from scutils.log_factory import LogFactory

logger = LogFactory.get_instance(
    json=False,
    stdout=False,
    level='DEBUG',
    name='aria2_dispatch',
    dir='logs',
    file='aria2_dispatch.log',
    bytes='1000MB',
    backups=5
)



def sha1(x):
    return hashlib.sha1(x).hexdigest()

class Aria2Dispatcher:
    def __init__(self, host, topic, consumer_id, settings):
        self.host = host
        self.topic = topic
        self.consumer_id = consumer_id or "Aria2Dispatcher"
        self.settings = importlib.import_module(settings[:-3])
        self.kafka_client = KafkaClient(self.settings.KAFKA_HOSTS)
        self.producer = SimpleProducer(self.kafka_client)
        self.topic_prefix = self.settings.KAFKA_TOPIC_PREFIX
        self.topic_list = []
        self.aria2_clients = []
        for x in self.settings.ARIA2_ADDRESSES:
            rpc_uri = "ws://%s/jsonrpc" % x
            try:
                aria2_connection=create_connection(rpc_uri)
                self.aria2_clients.append({
                	'rpc_uri': rpc_uri,
                	'ws': aria2_connection
            	})
            except:
                logger.error('create aria2_connection error!')
                raise


    def _process_item(self, item, aria2_client_index):

       
        prefix = self.topic_prefix
        crawled_firehose_images_topic = "{prefix}.crawled_firehose_images".format(prefix=prefix)


        if 'updates' in item['meta']['collection_name']:
            message = json.dumps(item)
            print("in.....   if 'updates' in item['meta']['collection_name']:")
            print('collection_name::',item['meta']['collection_name'])
        else:
            self._process_item_images(item, aria2_client_index)
            try:
                if 'images' in item and len(item['images']) > 0:
                    message = json.dumps(item)
                else:
                    message = 'no images.'
            except:
                message = 'json failed to parse'
                logger.error(message)

        self._check_topic(crawled_firehose_images_topic)
        self.producer.send_messages(crawled_firehose_images_topic, message)
        logger.info("send message to kafka topic:: %s " % crawled_firehose_images_topic)
        logger.info("message= %s" % message)

    def _process_item_images(self, item, aria2_client_index):
        image_urls = item["image_urls"]
        if len(image_urls) > 0:
            req_methods = []
            images = []
            for url in image_urls:
                filename, file_ext = splitext(basename(urlparse(url).path))
                if len(file_ext) == 0:
                    file_ext = ".jpg"

                out_file_name_base = sha1(url)
                out_file_name = "%s%s" % (out_file_name_base, file_ext)
                dir_name = '%s/%s/%s/%s/%s' % (self.settings.IMAGES_STORE,
                                               item['meta']['spiderid'],
                                               out_file_name_base[:3],
                                               out_file_name_base[3:6],
                                               out_file_name_base[6:])

                options = dict(
                    dir=dir_name,
                    out=out_file_name
                )
                if not exists(dir_name+'/'+out_file_name):
                    req_methods.append({"methodName": "aria2.addUri", "params": [[url], options]})

                images.append({
                    'url': url,
                    'path': "%s/%s" % (dir_name, out_file_name),
                    'aria2': {
                        'rpc_uri': self.aria2_clients[aria2_client_index]['rpc_uri']
                    }
                })

            req = {
                "jsonrpc": 2,
                "id": str(uuid.uuid1()),
                "method": "system.multicall",
                "params": [req_methods]
            }
            jsonreq = json.dumps(req)

            try:
                self.aria2_clients[aria2_client_index]['ws'].send(jsonreq)
                resp = self.aria2_clients[aria2_client_index]['ws'].recv()
                ws_resp = json.loads(resp)
                print('resp:', resp)
                logger.info('resp:: %s ' % resp)
                for image, gid in zip(images, map(lambda x: x[0], ws_resp['result'])):
                   image['aria2']['gid'] = gid

            except Exception as err:
                print('error::', err)
                logger.error(err)

            item['images'] = images

    def _check_topic(self, topic_name):
        if topic_name not in self.topic_list:
            self.kafka_client.ensure_topic_exists(topic_name)
            self.topic_list.append(topic_name)

    def dispatch(self):
        consumer = SimpleConsumer(
            self.kafka_client,
            self.consumer_id,
            self.topic,
            buffer_size=1024*100,       # 100kb
            fetch_size_bytes=1024*100,  # 100kb
            max_buffer_size=None        # eliminate big message errors
        )
        consumer.seek(0, 1)
        i = 0
        while True:
            try:
                message = consumer.get_message()
                if message is None:
                    print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ' message is None:'
                    logger.info('message is None.')
                    time.sleep(1)
                    continue
                val = message.message.value
                try:
                    item = json.loads(val)
                except:
                    print("error heppened in loads val: %s"%val)
                    logger.error("error heppened in loads val: %s"%val)
                    item = {"error":val}
                i += 1
                self._process_item(item, i % len(self.aria2_clients))
            except:
                traceback.print_exc()
                break

        self.kafka_client.close()
        return 0


def main():
    """
    Usage:
        aria2_dispatch --topic=<topic> --host=<host> --s=<s> [--consumer=<consumer>]
    """
    args = docopt(main.__doc__)
    host = args["--host"]
    topic = args["--topic"]
    consumer_id = args["--consumer"]
    settings = args["--s"]
    aria2_dispatcher = Aria2Dispatcher(host, topic, consumer_id, settings)
    return aria2_dispatcher.dispatch()

if __name__ == "__main__":
    sys.exit(main())
