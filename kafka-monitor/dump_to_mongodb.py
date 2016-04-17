from kafka import KafkaClient, SimpleConsumer
import json
import sys
import traceback
import logging
import time
import pymongo
from settings_kafkadump import MONGODB_DB, MONGODB_PORT, MONGODB_SERVER, IMAGES_STORE
from docopt import docopt

from scutils.log_factory import LogFactory

mongodb_server = MONGODB_SERVER
mongodb_port = MONGODB_PORT
mongodb_conn = pymongo.MongoClient(mongodb_server, mongodb_port)
mongodb_db = mongodb_conn[MONGODB_DB]


logger = LogFactory.get_instance(
    json=False,
    stdout=False,
    level='DEBUG',
    name='dump_to_mongodb',
    dir='logs',
    file='dump_to_mongodb.log',
    bytes='1000MB',
    backups=5
)

def _insert_item_to_monggodb(item):
    if 'meta' not in item:
        return
    try:
        collection = mongodb_db[item['meta']['collection_name']]
        collection.insert(item)
        print("item['meta']['collection_name']===", item['meta']['collection_name'])

        logger.info("item['meta']['collection_name']===%s" % item['meta']['collection_name'])

    except Exception as err:
        print('except Exception as err:')
        logger.error("err: %s" % err)


def main():
    """
    Usage:
        dump_to_mongodb dump <topic> --host=<host> [--consumer=<consumer>]
    """
    args = docopt(main.__doc__)
    host = args["--host"]

    print "=> Connecting to {0}...".format(host)
    logger.info("=> Connecting to {0}...".format(host))
    kafka = KafkaClient(host)
    print "=> Connected."
    logger.info("=> Connected.")
    if args["dump"]:
        topic = args["<topic>"]
        consumer_id = args["--consumer"] or "dump_to_mongodb"
        consumer = SimpleConsumer(kafka, consumer_id, topic,
                                  buffer_size=1024*200,      # 100kb
                                  fetch_size_bytes=1024*200, # 100kb
                                  max_buffer_size=None       # eliminate big message errors
                                  )
        consumer.seek(0, 1)
        while True:
            try:
                message = consumer.get_message()
                if message is None:
                    time.sleep(1)
                    continue
                val = message.message.value
                logger.info("message.message.value== %s " % val)
                print('val==', val)
                try:
                    item = json.loads(val)
                except:
                    continue
                if 'meta' in item and 'collection_name' in item['meta']:
                    _insert_item_to_monggodb(item)
            except:
                traceback.print_exc()
                break
        kafka.close()
        return 0

if __name__ == "__main__":
    sys.exit(main())
