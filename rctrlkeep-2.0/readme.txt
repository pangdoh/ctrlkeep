目前只支持命令行的交互模式

服务端：
server -host 绑定本地ip（默认0.0.0.0） -port 侦听本地端口（默认1234）
例：./server -host 0.0.0.0 -port 80

客户端：
client -host 连接远端ip -port远端端口 -always 设置断开重连间隔时间，单位秒（不加-always只连接一次，加参数但不写值默认间隔10秒） --daemon（守护进程方式启动）
例：./client -host 192.168.0.112 -port 80

本地命令：
\!q 结束本次连接
\!shutdown 结束目标进程