#!/bin/bash

NAME=crawl.sh

IP=`ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' |cut -d: -f2 | awk '{ print $1}'`
TARGET_DIR=target
PID_DIR=$TARGET_DIR/pid
LOG_DIR=$TARGET_DIR/logs

DIRS=($TARGET_DIR $PID_DIR $LOG_DIR)

SPIDERS=('amazon' 'eastbay' 'zappos' '6pm' 'drugstore' 'finishline' 'ashford' 'jacobtime')

case "$1" in
    start)
        echo "==== Start"
        for DIR in ${DIRS[@]}
        do
            mkdir -p $DIR
        done

        for SPIDER in ${SPIDERS[@]}
        do
            SSPIDER=${SPIDER}
            if [ -f $PID_DIR/${SPIDER}_$IP.pid ]
            then
                echo "$SSPIDER already started. PID: `cat $PID_DIR/$SSPIDER_$IP.pid`"
            else
                touch $PID_DIR/$SSPIDER_$IP.pid
                if nohup scrapy crawl ${SPIDER} --logfile=$LOG_DIR/${SPIDER}$IP.log > $TARGET_DIR/${SPIDER}$IP.stdout 2>&1 &
                then
                    echo $! > $PID_DIR/${SPIDER}$IP.pid
                    echo "$SSPIDER started."
                else
                    echo "$SSPIDER starting FAILED."
                fi
            fi
        done
        ;;
    stop)
        echo "==== Stop"
        for SPIDER in ${SPIDERS[@]}
        do
            SSPIDER=${SPIDER}
            if [ -f $PID_DIR/${SPIDER}$IP.pid ]
            then
                kill `cat $PID_DIR/${SPIDER}$IP.pid`
                rm $PID_DIR/${SPIDER}$IP.pid
                echo "$SSPIDER stopped."
            else
                echo "$SSPIDER: NO PID file found. Already stopped?"
            fi
        done
        ;;
    status)
        echo "==== Status"
        for SPIDER in ${SPIDERS[@]}
        do
            SSPIDER=${SPIDER}
            if [ -f $PID_DIR/${SPIDER}$IP.pid ]
            then
                echo "$SSPIDER: `cat $PID_DIR/${SPIDER}$IP.pid`"
            else
                echo "$SSPIDER: NO PID file found."
            fi
        done
        ;;
    *)
        echo "Usage: $NAME {start|stop|status}"
        ;;
esac
exit 0
