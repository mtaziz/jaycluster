import pickle
import sys
sys.path.append("../crawler")

class JayInfoMonitor():


    def setup(self,logger,redis_conn):
        '''
        Setup kafka
        '''
        self.logger = logger
        self.redis_conn = redis_conn

    def handle(self):
        '''
        Processes a vaild action info request

        @param key: The key that matched the request
        @param value: The value associated with the key
        '''
        # the master dict to return


        jay_info_func = {
            'jay_crawler_info': self.build_crawlid_info,
            'jay_spider_info': self.build_spider_info

        }

        # generate the information requested
        for key,func in jay_info_func.items():
            func()


    def _get_bin(self, key):
        '''
        Returns a binned dictionary based on redis zscore

        @return: The sorted dict
        '''
        # keys based on score
        sortedDict = {}
        # this doesnt return them in order, need to bin first
        for item in self.redis_conn.zscan_iter(key):
            my_item = pickle.loads(item[0])
            # score is negated in redis
            my_score = -item[1]

            if my_score not in sortedDict:
                sortedDict[my_score] = []

            sortedDict[my_score].append(my_item)

        return sortedDict

    def _build_appid_info(self, master, dict):
        '''
        Builds the appid info object

        @param master: the master dict
        @param dict: the dict object received
        @return: the appid info object
        '''
        master['total_crawlids'] = 0
        master['total_pending'] = 0
        master['total_domains'] = 0
        master['crawlids'] = {}
        master['appid'] = dict['appid']
        master['spiderid'] = dict['spiderid']

        # used for finding total count of domains
        domain_dict = {}

        # get all domain queues
        match_string = '{sid}:*:queue'.format(sid=dict['spiderid'])
        for key in self.redis_conn.scan_iter(match=match_string):
            domain = key.split(":")[1]
            sortedDict = self._get_bin(key)

            # now iterate through binned dict
            for score in sortedDict:
                for item in sortedDict[score]:
                    if 'meta' in item:
                        item = item['meta']
                    if item['appid'] == dict['appid']:
                        crawlid = item['crawlid']

                        # add new crawlid to master dict
                        if crawlid not in master['crawlids']:
                            master['crawlids'][crawlid] = {}
                            master['crawlids'][crawlid]['total'] = 0
                            master['crawlids'][crawlid]['domains'] = {}
                            master['crawlids'][crawlid]['distinct_domains'] = 0

                            timeout_key = 'timeout:{sid}:{aid}:{cid}'.format(
                                        sid=dict['spiderid'],
                                        aid=dict['appid'],
                                        cid=crawlid)
                            if self.redis_conn.exists(timeout_key):
                                master['crawlids'][crawlid]['expires'] = self.redis_conn.get(timeout_key)

                            master['total_crawlids'] = master['total_crawlids'] + 1

                        master['crawlids'][crawlid]['total'] = master['crawlids'][crawlid]['total'] + 1

                        if domain not in master['crawlids'][crawlid]['domains']:
                            master['crawlids'][crawlid]['domains'][domain] = {}
                            master['crawlids'][crawlid]['domains'][domain]['total'] = 0
                            master['crawlids'][crawlid]['domains'][domain]['high_priority'] = -9999
                            master['crawlids'][crawlid]['domains'][domain]['low_priority'] = 9999
                            master['crawlids'][crawlid]['distinct_domains'] = master['crawlids'][crawlid]['distinct_domains'] + 1
                            domain_dict[domain] = True


                        master['crawlids'][crawlid]['domains'][domain]['total'] = master['crawlids'][crawlid]['domains'][domain]['total'] + 1

                        if item['priority'] > master['crawlids'][crawlid]['domains'][domain]['high_priority']:
                            master['crawlids'][crawlid]['domains'][domain]['high_priority'] = item['priority']

                        if item['priority'] < master['crawlids'][crawlid]['domains'][domain]['low_priority']:
                            master['crawlids'][crawlid]['domains'][domain]['low_priority'] = item['priority']

                        master['total_pending'] = master['total_pending'] + 1

        master['total_domains'] = len(domain_dict)

        return master

    def build_crawlid_info(self):
        '''
        Builds the crawlid info object

        @param master: the master dict
        @param dict: the dict object received
        @return: the crawlid info object
        '''
        master = {}
        master['crawlerid'] = []
        master['crawlercount'] = 0

        # get all domain queues
        match_string = '*:*:queue'
        for key in self.redis_conn.scan_iter(match=match_string):
            spider = key.split(":")[0]

            sortedDict = self._get_bin(key)

            # now iterate through binned dict
            for score in sortedDict:
                for item in sortedDict[score]:
                    if 'meta' in item:
                        item = item['meta']

                    crawlid = item['crawlid']
                    if crawlid not in master['crawlerid']:
                        crawlerinfo = {}
                        crawlerinfo['crawler'] = {}
                        crawlerinfo['crawler']["crawlerid"] = crawlid
                        crawlerinfo['crawler']['total_pending'] = 0
                        master['crawlercount'] = master['crawlercount'] + 1




                    master['crawler'][crawlid]['total_pending'] = master['crawler'][crawlid]['total_pending']
            print(key, master)
            self.logger.info(key, extra=master)

    def build_spider_info(self):
        '''
        Builds the crawlid info object

        @param master: the master dict
        @param dict: the dict object received
        @return: the crawlid info object
        '''
        master = {}
        master['spidernames'] = []
        master['spidercount'] = 0


        # get all domain queues
        match_string = '*:*:queue'
        for key in self.redis_conn.scan_iter(match=match_string):
            spider = key.split(":")[0]
            spiderinfomation = {}
            spiderinfomation['spider']= {}
            spiderinfo = {}
            spiderinfo["spiderid"] = spider
            spiderinfo['total_pending'] = 0
            spiderinfo['crawlid'] = []
            spiderinfo['totalcrwalid'] = 0
            master['spidernames'].append(spider)
            master['spidercount'] = master['spidercount'] + 1
            sortedDict = self._get_bin(key)

            # now iterate through binned dict
            for score in sortedDict:
                for item in sortedDict[score]:
                    if 'meta' in item:
                        item = item['meta']

                    if item['crawlid'] not in spiderinfo['crawlid']:
                        spiderinfo['crawlid'].append(item['crawlid'])
                        spiderinfo['totalcrwalid'] = spiderinfo['totalcrwalid'] + 1

                        spiderinfo['total_pending'] = spiderinfo['total_pending'] + 1
            spiderinfomation['spider'].update(spiderinfo)
            print(key, spiderinfomation)
            self.logger.info(key, extra=spiderinfomation)

        print(master)
