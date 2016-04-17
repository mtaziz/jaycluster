# 1. 准备基本服务 #

## 1.1 redis server ##

``` bash
redis-server
```

## 1.2 zookeeper ##

``` bash
cd $KAFKA_HOME

sudo ./bin/zookeeper-server-start.sh ./config/zookeeper.properties

```

## 1.3 kafka broker ##

``` bash
cd $KAFKA_HOME

sudo ./bin/kafka-server-start.sh ./config/server.properties

```

# 2. 启动 scrapy cluster 服务 #

## 2.1 kafka monitor  ##
``` bash
cd $JAY_CLUSTER_HOME/kafka-monitor

python kafka-monitor.py run 
```

## 2.2 redis monitor ##

``` bash
cd $JAY_CLUSTER_HOME/kafka-monitor

python redis-monitor.py

```

## 2.3 启动 spiders ##

``` bash
cd $JAY_CLUSTER_HOME/crawler

scrapy crawl --logfile=<logfile_name.log> <spider_name>

```
# 3. 任务管理 #
## 3.1 添加一个 商品抓取 任务 ##

``` bash
cd $JAY_CLUSTER_HOME/kafka-monitor

python kafka_monitor.py feed '{ "url": "http://www.finishline.com/store/shop/men/shoes/training/_/N-33ida?categoryId=cat301585&mnid=men_shoes_training", "appid":"testapp", "crawlid":"abc123", "spiderid":"finishline", "callback":"parse"}' 

```

## 3.2添加一个 商品更新 任务 ##

``` bash
cd $JAY_CLUSTER_HOME/kafka-monitor


python kafka-monitor.py feed '{"url":"http://www.amazon.com/gp/product/B00GR4KBKC/ref=twister_dp_update?ie=UTF8&psc=1", "appid":"testapp", "crawlid":"abc123", "spiderid":"amazon", "callback":"parse_item_update","attrs":{"asin":"B00GR4KBKC"}}' 
```

## 3.3批量添加 商品更新 任务 ##

``` bash
cd $JAY_CLUSTER_HOME/kafka-monitor

python kafkafeed.py -appid=testapp -crawlid=testcrawlid -spiderid=amazon5 -urlsfile=urls.txt -fullurl=true 
```






##3.4 获取某个任务的信息 ##

TODO

## 3.5 停止某个任务 ##

TODO

4. 相关检查工具
4.1

``` bash
cd $JAY_CLUSTER_HOME/kafka-monitor

python kafkadump.py dump jay.crawled_firehose --host=127.0.0.1:9092

```

4.2

``` bash
cd $JAY_CLUSTER_HOME/kafka-monitor

python kafkadump.py dump jay.outbound_firehose --host=127.0.0.1:9092

```

4.3 把数据写入mongodb
``` bash
cd $JAY_CLUSTER_HOME/kafka-monitor

python dump_to_mongodb.py dump jay.crawled_firehose_images --host=127.0.0.1:9092

```
4.4 分发图片下载任务
``` bash
cd $JAY_CLUSTER_HOME/kafka-monitor

python aria2_dispatch.py --topic=jay.crawled_firehose --host=127.0.0.1:9092 --s=settings_aria2_dispatch.py


```



5. 注意事项

删除scraper_schema.json中spiderid的默认值
删除默认的 enum和 default
