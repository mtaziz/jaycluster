# -*- coding:utf-8 -*-
from redis import Redis
from bottle import template
from bottle import route, run
import pickle
redis_conn = Redis("192.168.200.90")
keys = "amazon_*:count_per_minute"
key_pattern = "amazon_dev_192-168-%s-160:count_per_minute"

tem = """<html>
            <head><titile></title>
                <script src="http://code.jquery.com/jquery-1.8.0.min.js" type="text/javascript"></script>
                <script>
                      $(document).ready(
                            function(){
                                $(".list").each(function(){
                                    that = $(this);
                                    $.ajax({
                                        url:"/pi/"+/amazon_(?:\w+)_192-168-(\d+)-(?:\d+)/.exec($(this).attr("id"))[1],
                                        success:succed,
                                        error:errored
                                    })
                                    setInterval("flash()", 60*1000)
                                });
                            }
                        );

                        function succed(data){
                            var data = eval("("+data+")");
                            for(var li in data){
                                str = "<li>"+li+":"
                                for(i=0;i<data[li];i++){
                                    str += "1";
                                }
                                str += "</li>"
                                var li = $(str)
                                that.prepend(li);

                            }
                        }

                        function errored(){
                            alert("failed");
                        }

                        function flash(){
                            var time = getDate()
                            $.ajax({
                                url:"/pi/"+/amazon_(?:\w+)_192-168-(\d+)-(?:\d+)/.exec(that.attr("id"))[1]+"/"+time,
                                success:succed,
                                error:errored
                            })
                        }

                        function getDate(){
                            var d = new Date();
                            var vYear = d.getFullYear();
                            var vMon = d.getMonth()+1<10?"0"+(d.getMonth()+1):d.getMonth()+1;
                            var vDay = d.getDate()<10?"0"+d.getDate():d.getDate();
                            var h = d.getHours()<10?"0"+d.getHours():d.getHours();
                            var m = d.getMinutes()<10?"0"+d.getMinutes():d.getMinutes();
                            return ""+vYear+vMon+vDay+h+m
                        }
                </script>
            </head>
            <body>
                % for key in keys:
                    <p>{{key}}</p>
                    <ul class="list" id="{{key}}" >
                    </ul>
                % end
            </body>
        </html>"""

@route("/")
def index():
    k = redis_conn.keys(keys)
    print(">>>>>", k)
    return template(tem, keys=k)

@route("/pi/<pi:int:>/<time::>")
def status(pi, time):
    msg = redis_conn.hget(key_pattern % pi, time)
    return str({time:pickle.loads(msg)} if msg else {time:0})

@route("/pi/<pi:int:>")
def statusall(pi):
    dic = redis_conn.hgetall(key_pattern%pi)
    for key in dic:
        dic[key] = pickle.loads(dic[key])
    return str(dic)

if __name__ == "__main__":
    run(host="192.168.200.58", debug=True, reloader=True)


