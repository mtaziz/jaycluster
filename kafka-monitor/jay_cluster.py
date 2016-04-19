import argparse
import sys

from crawler.crawling.kafka_monitor_sdk import feed

"""
Usage:
  python jay_cluster.py
  >>feed -json {"url":"http://www.finishline.com/store/shop/men/shoes/training/_/N-33ida?categoryId=cat301585&mnid=men_shoes_training","appid":"testapp","crawlid":"abc123","spiderid":"finishline","callback":"parse"} -s settings_crawling.py
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', type=str, nargs=1)
    parser.add_argument('-json', type=str)
    parser.add_argument('-s', type=str)
    while True:
        try:
            cmd = raw_input('>>')
            try:
                args = parser.parse_args(args=(' '.join(cmd.split())).split())
            except:
                print('unrecognized arguments')
                continue
        except EOFError:
                print 'exit'
                exit(0)
        except KeyboardInterrupt:
                print 'type "exit" to exit'
                continue
        if "feed" in args.cmd:
            feed(args.s, args.json)
        elif "exit" in args.cmd:
            exit(0)


if __name__ == "__main__":
    sys.exit(main())
