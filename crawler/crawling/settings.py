# This file houses all default settings for the Crawler
# to override please use a custom localsettings.py file

# Scrapy Cluster Settings
# ~~~~~~~~~~~~~~~~~~~~~~~
import pkgutil

# Specify the host and port to use when connecting to Redis.
REDIS_HOST = '192.168.56.6'
REDIS_PORT = '6379'

# Kafka server information
KAFKA_HOSTS = '192.168.56.6:9092'
KAFKA_TOPIC_PREFIX = 'jay'
KAFKA_APPID_TOPICS = False
# base64 encode the html body to avoid json dump errors due to malformed text
KAFKA_BASE_64_ENCODE = False

ZOOKEEPER_ASSIGN_PATH = '/scrapy-cluster/crawler/'
ZOOKEEPER_ID = 'all'
ZOOKEEPER_HOSTS = '192.168.56.6:2181'

PUBLIC_IP_URL = 'http://ip.42.pl/raw'
IP_ADDR_REGEX = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'

# Don't cleanup redis queues, allows to pause/resume crawls.
SCHEDULER_PERSIST = True

# seconds to wait between seeing new queues, cannot be faster than spider_idle time of 5
SCHEDULER_QUEUE_REFRESH = 10

# throttled queue defaults per domain, x hits in a y second window
QUEUE_HITS = 100
QUEUE_WINDOW = 60

# we want the queue to produce a consistent pop flow
QUEUE_MODERATED = True

# how long we want the duplicate timeout queues to stick around in seconds
DUPEFILTER_TIMEOUT = 600

# how often to refresh the ip address of the scheduler
SCHEDULER_IP_REFRESH = 60


USER_AGENT_LIST = pkgutil.get_data('crawling', 'user_agents.list')

'''
----------------------------------------
The below parameters configure how spiders throttle themselves across the cluster
All throttling is based on the TLD of the page you are requesting, plus any of the
following parameters:

Type: You have different spider types and want to limit how often a given type of
spider hits a domain

IP: Your crawlers are spread across different IP's, and you want each IP crawler clump
to throttle themselves for a given domain

Combinations for any given Top Level Domain:
None - all spider types and all crawler ips throttle themselves from one tld queue
Type only - all spiders throttle themselves based off of their own type-based tld queue,
    regardless of crawler ip address
IP only - all spiders throttle themselves based off of their public ip address, regardless
    of spider type
Type and IP - every spider's throttle queue is determined by the spider type AND the
    ip address, allowing the most fined grained control over the throttling mechanism
'''
# add Spider type to throttle mechanism
SCHEDULER_TYPE_ENABLED = True

# add ip address to throttle mechanism
SCHEDULER_IP_ENABLED = True
'''
----------------------------------------
'''

# how many times to retry getting an item from the queue before the spider is considered idle
SCHEUDLER_ITEM_RETRIES = 3

# log setup scrapy cluster crawler
SC_LOGGER_NAME = 'sc-crawler'
SC_LOG_DIR = 'logs'
SC_LOG_FILE = 'sc_crawler.log'
SC_LOG_MAX_BYTES = '10MB'
SC_LOG_BACKUPS = 5
SC_LOG_STDOUT = False
SC_LOG_JSON = True
SC_LOG_LEVEL = 'DEBUG'


# stats setup
STATS_STATUS_CODES = True
STATS_RESPONSE_CODES = [
    200,
    404,
    403,
    504,
]
STATS_CYCLE = 5
# from time variables in scutils.stats_collector class
STATS_TIMES = [
    'SECONDS_15_MINUTE',
    'SECONDS_1_HOUR',
    'SECONDS_6_HOUR',
    'SECONDS_12_HOUR',
    'SECONDS_1_DAY',
    'SECONDS_1_WEEK',
]

# Scrapy Settings
# ~~~~~~~~~~~~~~~
DOWNLOADER_CLIENTCONTEXTFACTORY = 'crawling.contextfactory.MyClientContextFactory'

# Scrapy settings for distributed_crawling project
#
BOT_NAME = 'crawling'

SPIDER_MODULES = ['crawling.spiders']
NEWSPIDER_MODULE = 'crawling.spiders'

# Enables scheduling storing requests queue in redis.
SCHEDULER = "crawling.distributed_scheduler.DistributedScheduler"

STATS_CLASS = 'crawling.my_stats_collectors.MyStatsCollector'


# Store scraped item in redis for post-processing.
ITEM_PIPELINES = {
    'crawling.pipelines.KafkaPipeline': 100,
    'crawling.pipelines.LoggingBeforePipeline': 1,
    'crawling.pipelines.LoggingAfterPipeline': 101,
}

SPIDER_MIDDLEWARES = {
    # disable built-in DepthMiddleware, since we do our own
    # depth management per crawl request
    'scrapy.contrib.spidermiddleware.depth.DepthMiddleware': None,
}

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'crawling.downloadermiddlewares.RandomUserAgentMiddleware': 400,



    # Handle timeout retries with the redis scheduler and logger
    # 'scrapy.contrib.downloadermiddleware.retry.RetryMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware':None,
    'crawling.redis_retry_middleware.RedisRetryMiddleware': 510,
    # exceptions processed in reverse order
    'crawling.log_retry_middleware.LogRetryMiddleware': 520,
    # custom cookies to not persist across crawl requests
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
    'crawling.costom_redirect_middleware.CustomRedirectMiddleware': 600,
    # 'scrapy.contrib.downloadermiddleware.cookies.CookiesMiddleware': None,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    'crawling.custom_cookies.CustomCookiesMiddleware': 700,
    'scrapy.downloadermiddlewares.stats.DownloaderStats': None,
    'crawling.download_stats.CostomDownloaderStats': 850,
}

# Disable the built in logging in production
LOG_ENABLED = True

# Allow all return codes
HTTPERROR_ALLOW_ALL = True

RETRY_TIMES = 3

DOWNLOAD_TIMEOUT = 30

# Avoid in-memory DNS cache. See Advanced topics of docs for info
DNSCACHE_ENABLED = True



MONGODB_SERVER = '192.168.56.6'
MONGODB_PORT = 27017
MONGODB_DB = 'products'

################# Aria2 ###################
IMAGES_STORE = '/home/chuande/project/aria2/images'
ARIA2_ADDRESSES = ['192.168.56.6:6900']


# Local Overrides
# ~~~~~~~~~~~~~~~

try:
    from localsettings import *
except ImportError:
    pass
