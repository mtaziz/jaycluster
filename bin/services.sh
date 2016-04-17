#!/bin/bash
NAME=services.sh
JAY_CLUSTER_HOME=`pwd`

KAFKA_MONITOR_PID_DIR=$JAY_CLUSTER_HOME/kafka-monitor/pid
KAFKA_MONITOR_LOG_DIR=$JAY_CLUSTER_HOME/kafka-monitor/logs
KAFKA_MONITOR_STDOUT_DIR=$JAY_CLUSTER_HOME/kafka-monitor/stdout

REDIS_MONITOR_PID_DIR=$JAY_CLUSTER_HOME/redis-monitor/pid
REDIS_MONITOR_LOG_DIR=$JAY_CLUSTER_HOME/redis-monitor/logs
REDIS_MONITOR_STDOUT_DIR=$JAY_CLUSTER_HOME/redis-monitor/stdout
 
ARIA2_DISPATCH_PID_DIR=$JAY_CLUSTER_HOME/kafka-monitor/pid
ARIA2_DISPATCH_STDOUT_DIR=$JAY_CLUSTER_HOME/kafka-monitor/stdout

DUMP_TO_MONGODB_PID_DIR=$JAY_CLUSTER_HOME/kafka-monitor/pid
DUMP_TO_MONGODB_STDOUT_DIR=$JAY_CLUSTER_HOME/kafka-monitor/stdout

DIRS=($KAFKA_MONITOR_PID_DIR $KAFKA_MONITOR_LOG_DIR $KAFKA_MONITOR_STDOUT_DIR $REDIS_MONITOR_PID_DIR $REDIS_MONITOR_LOG_DIR $REDIS_MONITOR_STDOUT_DIR)

KAFKA_MONITOR='kafka_monitor'
REDIS_MONITOR='redis_monitor'
ARIA2_DISPATCH='aria2_dispatch'
DUMP_TO_MONGODB='dump_to_mongodb'

case "$1" in
    start)
        echo "==== Start"
        for DIR in ${DIRS[@]}
        do
            mkdir -p $DIR
        done
        
		cd kafka-monitor	  
        if [ -f $KAFKA_MONITOR_PID_DIR/$KAFKA_MONITOR.pid ]
        then
            echo "$KAFKA_MONITOR already started. PID: `cat $KAFKA_MONITOR_PID_DIR/$KAFKA_MONITOR.pid`"
		else
			touch $KAFKA_MONITOR_PID_DIR/$KAFKA_MONITOR.pid		
			if nohup python kafka_monitor.py run -lf -lj> $KAFKA_MONITOR_STDOUT_DIR/$KAFKA_MONITOR.stdout 2>&1 &
			then
				echo $! > $KAFKA_MONITOR_PID_DIR/$KAFKA_MONITOR.pid
				echo "$KAFKA_MONITOR started."
			else
				echo "$KAFKA_MONITOR starting FAILED."
			fi
		fi
		
		if [ -f $ARIA2_DISPATCH_PID_DIR/$ARIA2_DISPATCH.pid ]
        then
            echo "$ARIA2_DISPATCH already started. PID: `cat $ARIA2_DISPATCH_PID_DIR/$ARIA2_DISPATCH.pid`"
		else
			touch $ARIA2_DISPATCH_PID_DIR/$ARIA2_DISPATCH.pid 
			if nohup python aria2_dispatch.py --topic=jay.crawled_firehose --host=192.168.200.90:9092 --s=settings_aria2_dispatch.py> $ARIA2_DISPATCH_STDOUT_DIR/$ARIA2_DISPATCH.stdout 2>&1 &
			then
				echo $! > $ARIA2_DISPATCH_PID_DIR/$ARIA2_DISPATCH.pid 
				echo "$ARIA2_DISPATCH started."
			else
				echo "$ARIA2_DISPATCH starting FAILED."
			fi
		fi
		
		
		if [ -f $DUMP_TO_MONGODB_PID_DIR/$DUMP_TO_MONGODB.pid ]
        then
            echo "$DUMP_TO_MONGODB already started. PID: `cat $DUMP_TO_MONGODB_PID_DIR/$DUMP_TO_MONGODB.pid`"
		else		 
			if nohup python dump_to_mongodb.py dump jay.crawled_firehose_images --host=192.168.200.90:9092> $DUMP_TO_MONGODB_STDOUT_DIR/$DUMP_TO_MONGODB.stdout 2>&1 &
			then
				echo $! > $DUMP_TO_MONGODB_PID_DIR/$DUMP_TO_MONGODB.pid
				echo "$DUMP_TO_MONGODB started."
			else
				echo "$DUMP_TO_MONGODB starting FAILED."
			fi			
		fi	
		
		if [ -f $REDIS_MONITOR_PID_DIR/$REDIS_MONITOR.pid ]
        then
            echo "$REDIS_MONITOR already started. PID: `cat $REDIS_MONITOR_PID_DIR/$REDIS_MONITOR.pid`"
		else		 
			if nohup python $JAY_CLUSTER_HOME/redis-monitor/redis_monitor.py -lf -lj> $REDIS_MONITOR_STDOUT_DIR/$REDIS_MONITOR.stdout 2>&1 &
			then
				echo $! > $REDIS_MONITOR_PID_DIR/$REDIS_MONITOR.pid
				echo "$REDIS_MONITOR started."
			else
				echo "$REDIS_MONITOR starting FAILED."
			fi			
		fi      
        ;;
    stop)
        echo "==== Stop"
		
		echo $KAFKA_MONITOR_PID_DIR/$KAFKA_MONITOR.pid	 
		if [ -f $KAFKA_MONITOR_PID_DIR/$KAFKA_MONITOR.pid ]
		then
			kill `cat $KAFKA_MONITOR_PID_DIR/$KAFKA_MONITOR.pid`
			rm $KAFKA_MONITOR_PID_DIR/$KAFKA_MONITOR.pid
			echo "$KAFKA_MONITOR stopped."
		else
			echo "$KAFKA_MONITOR: NO PID file found. Already stopped?"
		fi		
		
		echo $REDIS_MONITOR_PID_DIR/$REDIS_MONITOR.pid	 
		if [ -f $REDIS_MONITOR_PID_DIR/$REDIS_MONITOR.pid ]
		then
			kill `cat $REDIS_MONITOR_PID_DIR/$REDIS_MONITOR.pid`
			rm $REDIS_MONITOR_PID_DIR/$REDIS_MONITOR.pid
			echo "$REDIS_MONITOR stopped."
		else
			echo "$REDIS_MONITOR: NO PID file found. Already stopped?"
		fi
		
		echo $ARIA2_DISPATCH_PID_DIR/$ARIA2_DISPATCH.pid	 
		if [ -f $ARIA2_DISPATCH_PID_DIR/$ARIA2_DISPATCH.pid ]
		then
			kill `cat $ARIA2_DISPATCH_PID_DIR/$ARIA2_DISPATCH.pid`
			rm $ARIA2_DISPATCH_PID_DIR/$ARIA2_DISPATCH.pid
			echo "$ARIA2_DISPATCH stopped."
		else
			echo "$ARIA2_DISPATCH: NO PID file found. Already stopped?"
		fi
		
		echo $DUMP_TO_MONGODB_PID_DIR/$DUMP_TO_MONGODB.pid	 
		if [ -f $DUMP_TO_MONGODB_PID_DIR/$DUMP_TO_MONGODB.pid ]
		then
			kill `cat $DUMP_TO_MONGODB_PID_DIR/$DUMP_TO_MONGODB.pid`
			rm $DUMP_TO_MONGODB_PID_DIR/$DUMP_TO_MONGODB.pid
			echo "$DUMP_TO_MONGODB stopped."
		else
			echo "$DUMP_TO_MONGODB: NO PID file found. Already stopped?"
		fi      
        ;;
    status)
        echo "======================= Status ======================="
			 
		if [ -f $KAFKA_MONITOR_PID_DIR/$KAFKA_MONITOR.pid ]
		then
			PID=`cat $KAFKA_MONITOR_PID_DIR/$KAFKA_MONITOR.pid`
			echo ""
			echo ""
			echo "$KAFKA_MONITOR: $PID"
			echo `ps -aux|head -1`
			echo `ps -aux|grep $PID|grep -v grep`
		else
			echo "$KAFKA_MONITOR: NO PID file found."
		fi		
		
		if [ -f $ARIA2_DISPATCH_PID_DIR/$ARIA2_DISPATCH.pid ]
		then
			PID=`cat $ARIA2_DISPATCH_PID_DIR/$ARIA2_DISPATCH.pid`
			echo ""
			echo ""
			echo "$ARIA2_DISPATCH: $PID"
			echo `ps -aux|head -1`
			echo `ps -aux|grep $PID|grep -v grep`
		else
			echo "$ARIA2_DISPATCH: NO PID file found."
		fi		
		
        if [ -f $REDIS_MONITOR_PID_DIR/$REDIS_MONITOR.pid ]
		then
			PID=`cat $REDIS_MONITOR_PID_DIR/$REDIS_MONITOR.pid`
			echo ""
			echo ""
			echo "$REDIS_MONITOR: $PID"
			echo `ps -aux|head -1`
			echo `ps -aux|grep $PID|grep -v grep`
		else
			echo "$REDIS_MONITOR: NO PID file found."
		fi
		
		if [ -f $DUMP_TO_MONGODB_PID_DIR/$DUMP_TO_MONGODB.pid ]
		then
			PID=`cat $DUMP_TO_MONGODB_PID_DIR/$DUMP_TO_MONGODB.pid`
			echo ""
			echo ""
			echo "$DUMP_TO_MONGODB: $PID"
			echo `ps -aux|head -1`
			echo `ps -aux|grep $PID|grep -v grep`
		else
			echo "$DUMP_TO_MONGODB: NO PID file found."
		fi	
		
		echo ""		
	
        ;;
    *)
	    echo "Usage: $ sudo bash ./bin/services.sh {start|stop|status}"
        echo "Usage: $NAME {start|stop|status}"
        ;;
esac
exit 0
