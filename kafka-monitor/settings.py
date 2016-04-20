# This file houses all default settings for the Kafka Monitor
# to override please use a custom localsettings.py file

# Redis host information
REDIS_HOST = '192.168.56.6'
REDIS_PORT = 6379

# Kafka server information
KAFKA_HOSTS = '192.168.56.6:9092'

KAFKA_INCOMING_TOPIC = 'jay.incoming'
KAFKA_GROUP = 'jay-group'
KAFKA_FEED_TIMEOUT = 5
KAFKA_CONN_TIMEOUT = 5

# plugin setup
PLUGIN_DIR = 'plugins/'
PLUGINS = {
    'plugins.scraper_handler.ScraperHandler': 100,
    'plugins.action_handler.ActionHandler': 200,
    'plugins.stats_handler.StatsHandler': 300,
}

# logging setup
LOGGER_NAME = 'kafka-monitor'
LOG_DIR = 'logs'
LOG_FILE = 'kafka_monitor.log'
LOG_MAX_BYTES = '10MB'
LOG_BACKUPS = 5
LOG_STDOUT = False
LOG_JSON = True
LOG_LEVEL = 'INFO'

# stats setup
STATS_TOTAL = True
STATS_PLUGINS = True
STATS_CYCLE = 5
STATS_DUMP = 60
# from time variables in scutils.stats_collector class
STATS_TIMES = [
    'SECONDS_15_MINUTE',
    'SECONDS_1_HOUR',
    'SECONDS_6_HOUR',
    'SECONDS_12_HOUR',
    'SECONDS_1_DAY',
    'SECONDS_1_WEEK',
]
