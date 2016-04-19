#!/usr/bin/python

from kafka.client import KafkaClient
from kafka.producer import SimpleProducer
import json
import importlib
from kafka_monitor import KafkaMonitor


__KafkaMonitor = KafkaMonitor(settings_name='localsettings.py')

__KafkaMonitor.setup()



def _feed(settings_file, json_item):
    settings = importlib.import_module(settings_file[:-3])
    kafka_conn = KafkaClient(settings.KAFKA_HOSTS)
    topic = settings.KAFKA_INCOMING_TOPIC
    producer = SimpleProducer(kafka_conn)
    print "=> feeding JSON request into {0}...".format(topic)
    print json.dumps(json_item, indent=4)
    kafka_conn.ensure_topic_exists(topic)
    producer.send_messages(topic, json.dumps(json_item))
    print "=> done feeding request."


def feed(settings_file, json_req):
    print('json_req==', json_req)

    try:
        parsed = json.loads(json_req)
    except ValueError:
        print "json failed to parse"
        return 1
    else:
        return __KafkaMonitor.feed(parsed)
=======
#!/usr/bin/python

from kafka.client import KafkaClient
from kafka.producer import SimpleProducer
import json
import importlib
from kafka_monitor import KafkaMonitor


__KafkaMonitor = KafkaMonitor(settings_name='localsettings.py')

__KafkaMonitor.setup()



def _feed(settings_file, json_item):
    settings = importlib.import_module(settings_file[:-3])
    kafka_conn = KafkaClient(settings.KAFKA_HOSTS)
    topic = settings.KAFKA_INCOMING_TOPIC
    producer = SimpleProducer(kafka_conn)
    print "=> feeding JSON request into {0}...".format(topic)
    print json.dumps(json_item, indent=4)
    kafka_conn.ensure_topic_exists(topic)
    producer.send_messages(topic, json.dumps(json_item))
    print "=> done feeding request."


def feed(settings_file, json_req):
    print('json_req==', json_req)

    try:
        parsed = json.loads(json_req)
    except ValueError:
        print "json failed to parse"
        return 1
    else:
        return __KafkaMonitor.feed(parsed)
>>>>>>> 2b6efcc4b238665fcb7cf1940aeee3138361a825
