
class JayStatsMonitor():

    def setup(self,logger,redis_conn):
        '''
        Setup kafka
        '''
        self.logger = logger
        self.redis_conn = redis_conn

    def handle(self):
        '''
        Processes a vaild stats request

        @param key: The key that matched the request
        @param value: The value associated with the key
        '''
        # break down key

        extras = {}

        jay_stats_func = {
            'kafka-monitor-stats': self.get_kafka_monitor_stats,
            'redis-monitor-stats': self.get_redis_monitor_stats,
            'crawler-stats': self.get_crawler_stats,
            'spider-stats': self.get_spider_stats,
            'machine-stats': self.get_machine_stats

        }

        for key, func in jay_stats_func.items():
            dict = func()
            self.logger.info(key, extra=dict)


    def get_all_stats(self):
        '''
        Gather all stats objects
        '''
        self.logger.debug("Gathering all stats")
        the_dict = {}
        the_dict['kafka-monitor'] = self.get_kafka_monitor_stats()
        the_dict['redis-monitor'] = self.get_redis_monitor_stats()
        the_dict['crawler'] = self.get_crawler_stats()

        return the_dict


    def get_kafka_monitor_stats(self):
        '''
        Gather Kafka Monitor stats

        @return: A dict of stats
        '''
        self.logger.debug("Gathering kafka-monitor stats")
        return self._get_plugin_stats('kafka-monitor')


    def get_redis_monitor_stats(self):
        '''
        Gather Redis Monitor stats

        @return: A dict of stats
        '''
        self.logger.debug("Gathering redis-monitor stats")
        return self._get_plugin_stats('redis-monitor')


    def _get_plugin_stats(self, name):
        '''
        Used for getting stats for Plugin based stuff, like Kafka Monitor
        and Redis Monitor

        @param name: the main class stats name
        @return: A formatted dict of stats
        '''
        the_dict = {}

        keys = self.redis_conn.keys('stats:{n}:*'.format(n=name))

        for key in keys:
            # break down key
            elements = key.split(":")
            main = elements[2]
            end = elements[3]

            if main == 'total' or main == 'fail':
                if main not in the_dict:
                    the_dict[main] = {}
                the_dict[main][end] = self._get_key_value(key, end == 'lifetime')

            else:
                if 'plugins' not in the_dict:
                    the_dict['plugins'] = {}
                if main not in the_dict['plugins']:
                    the_dict['plugins'][main] = {}
                the_dict['plugins'][main][end] = self._get_key_value(key, end == 'lifetime')

        return the_dict


    def _get_key_value(self, key, is_hll=False):
        '''
        Returns the proper key value for the stats

        @param key: the redis key
        @param is_hll: the key is a HyperLogLog, else is a sorted set
        '''
        if is_hll:
            # get hll value
            return self.redis_conn.execute_command("PFCOUNT", key)
        else:
            # get zcard value
            return self.redis_conn.zcard(key)


    def get_spider_stats(self):
        '''
        Gather spider based stats
        '''
        self.logger.debug("Gathering spider stats")
        the_dict = {}
        spider_set = set()
        total_spider_count = 0

        keys = self.redis_conn.keys('stats:crawler:*:*:*')
        for key in keys:
            # we only care about the spider
            elements = key.split(":")
            spider = elements[3]

            if spider not in the_dict:
                the_dict[spider] = {}
                the_dict[spider]['count'] = 0

            if len(elements) == 6:
                # got a time based stat
                response = elements[4]
                end = elements[5]

                if response not in the_dict[spider]:
                    the_dict[spider][response] = {}

                the_dict[spider][response][end] = self._get_key_value(key, end == 'lifetime')

            elif len(elements) == 5:
                # got a spider identifier
                the_dict[spider]['count'] += 1
                total_spider_count += 1
                spider_set.add(spider)

            else:
                self.logger.warn("Unknown crawler stat key", {"key": key})

        # simple counts
        the_dict['unique_spider_count'] = len(spider_set)
        the_dict['total_spider_count'] = total_spider_count

        ret_dict = {}
        ret_dict['spiders'] = the_dict

        return ret_dict


    def get_machine_stats(self):
        '''
        Gather spider based stats
        '''
        self.logger.debug("Gathering machine stats")
        the_dict = {}
        keys = self.redis_conn.keys('stats:crawler:*:*:*:*')
        for key in keys:
            # break down key
            elements = key.split(":")
            machine = elements[2]
            spider = elements[3]
            response = elements[4]
            end = elements[5]

            # we only care about the machine, not spider type
            if machine not in the_dict:
                the_dict[machine] = {}

            if response not in the_dict[machine]:
                the_dict[machine][response] = {}

            if end in the_dict[machine][response]:
                the_dict[machine][response][end] = the_dict[machine][response][end] + \
                                                   self._get_key_value(key, end == 'lifetime')
            else:
                the_dict[machine][response][end] = self._get_key_value(key, end == 'lifetime')

        # simple count
        the_dict['count'] = len(the_dict.keys())

        ret_dict = {}
        ret_dict['machines'] = the_dict

        return ret_dict


    def get_crawler_stats(self):
        '''
        Gather crawler stats

        @return: A dict of stats
        '''
        self.logger.debug("Gathering crawler stats")
        the_dict = {}

        the_dict['spiders'] = self.get_spider_stats()['spiders']
        the_dict['machines'] = self.get_machine_stats()['machines']

        return the_dict

