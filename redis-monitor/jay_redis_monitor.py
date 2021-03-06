import redis
import sys
import traceback
import argparse
import time
import json

from collections import OrderedDict
from scutils.log_factory import LogFactory
from scutils.settings_wrapper import SettingsWrapper
from scutils.stats_collector import StatsCollector
from redis.exceptions import ConnectionError
from   jay_redis_stats import JayStatsMonitor
from jay_redis_info import JayInfoMonitor


class JayRedisMonitor:

    def __init__(self, settings_name, unit_test=False):
        '''
        @param settings_name: the local settings file name
        @param unit_test: whether running unit tests or not
        '''
        self.settings_name = settings_name
        self.redis_conn = None
        self.wrapper = SettingsWrapper()
        self.logger = None
        self.unit_test = unit_test

    def setup(self, level=None, log_file=None, json=None):
        '''
        Load everything up. Note that any arg here will override both
        default and custom settings

        @param level: the log level
        @param log_file: boolean t/f whether to log to a file, else stdout
        @param json: boolean t/f whether to write the logs in json
        '''
        self.settings = self.wrapper.load(self.settings_name)

        my_level = level if level else self.settings['LOG_LEVEL']
        # negate because logger wants True for std out
        my_output = not log_file if log_file else self.settings['LOG_STDOUT']
        my_json = json if json else self.settings['LOG_JSON']
        self.logger = LogFactory.get_instance(json=my_json,
                                              stdout=my_output,
                                              level=my_level,
                                              #name=self.settings['LOGGER_NAME'],
                                              name = "jay-redis-monitor",
                                              dir=self.settings['LOG_DIR'],
                                              #file=self.settings['LOG_FILE'],
                                              file="jay_redis_monitor.log",
                                              bytes=self.settings['LOG_MAX_BYTES'],
                                              backups=self.settings['LOG_BACKUPS'])

        self.redis_conn = redis.Redis(host=self.settings['REDIS_HOST'],
                                      port=self.settings['REDIS_PORT'])
        try:
            self.redis_conn.info()
            self.logger.debug("Successfully connected to Redis")
        except ConnectionError:
            self.logger.error("Failed to connect to Redis")
            # essential to functionality
            sys.exit(1)



    def run(self):
        '''
        The external main run loop
        '''
        self._main_loop()

    def _main_loop(self):
        '''
        The internal while true main loop for the redis monitor
        '''
        self.logger.debug("Running main loop")
        print 'Running main loop'
        jaystats = JayStatsMonitor()
        jaystats.setup(self.logger,self.redis_conn)
        jayinfo = JayInfoMonitor()
        jayinfo.setup(self.logger,self.redis_conn)

        while True:
            jaystats.handle()
            jayinfo.handle()




            time.sleep(1)



def main():
    parser = argparse.ArgumentParser(
        description='Redis Monitor: Monitor the Scrapy Cluster Redis '
        'instance.\n')

    parser.add_argument('-s', '--settings', action='store', required=False,
                        help="The settings file to read from",
                        default="localsettings.py")
    parser.add_argument('-ll', '--log-level', action='store', required=False,
                        help="The log level", default=None,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    parser.add_argument('-lf', '--log-file', action='store_const',
                        required=False, const=True, default=None,
                        help='Log the output to the file specified in '
                        'settings.py. Otherwise logs to stdout')
    parser.add_argument('-lj', '--log-json', action='store_const',
                        required=False, const=True, default=None,
                        help="Log the data in JSON format")
    args = vars(parser.parse_args())

    redis_monitor = JayRedisMonitor(args['settings'])
    redis_monitor.setup(level=args['log_level'], log_file=args['log_file'],
                        json=args['log_json'])
    try:
        redis_monitor.run()
    except KeyboardInterrupt:
        redis_monitor.logger.info("Closing Redis Monitor")

if __name__ == "__main__":
    sys.exit(main())
