import socket
import threading
import queue
import json  # json.dumps(some)打包   json.loads(some)解包
import time
import os
import os.path
import sys
import struct
import hashlib
import re

IP = ''
PORT = 50007
que = queue.Queue()  # 用于存放客户端发送的信息的队列(其中有str和userlist两种信息)
users = []  # 用于存放在线用户的信息  [conn, user, addr]  conn是socket对象
lock = threading.Lock()  # 创建锁, 防止多个线程写入数据的顺序打乱


# 将在线用户存入online列表并返回
def onlines():
    online = []
    for i in range(len(users)):
        online.append(users[i][1])
    return online


class ChatServer(threading.Thread):  # 继承Thread类
    global users, que, lock

    # 构造函数
    def __init__(self, port):
        threading.Thread.__init__(self)  # 首先初始化Thread
        self.ADDR = ('', port)  # self.s.bind(self.ADDR)，不设置ip用''表示默认为本机IP
        # os.chdir() 方法用于改变当前工作目录到指定的路径。
        # sys.path是python的搜索模块的路径集,path[0],在程序启动时初始化，是包含用来调用Python解释器的脚本的目录
        os.chdir(sys.path[0])
        # AF_INET : 用于服务器与服务器之间的网络通信
        # SOCK_STREAM : 基于TCP的流式socket通信
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 用于接收所有客户端发送信息的函数
    # conn 是连接返回的socket,addr是(ip,port)集合
    def tcp_connect(self, conn, addr):
        # 连接后将用户信息添加到users列表
        user = conn.recv(1024)  # 接收 TCP 数据，数据以字符串形式返回
        print(type(user))
        user = user.decode()  # decode()默认为字符串编码
        # 查找是否有重复字符串元素，users存放所有在线用户信息
        for i in range(len(users)):
            if user == users[i][1]:
                print('User already exist')
                user = '' + user + '_2'
        if user == 'no':  # 登录用户名是no，用户名改成客户端ip:port
            user = addr[0] + ':' + str(addr[1])
        users.append((conn, user, addr))
        print(' New connection:', addr, ':', user, end=' ')  # 打印用户名
        d = onlines()  # 有新连接则刷新客户端的在线用户显示
        # tcp每次建立连接时先将当前的所有online用户信息全部放入到queue,之后再处理其他信息
        self.recv(d, addr)  # 这个recv是类里自己定义的函数
        try:
            while True:
                data = conn.recv(1024)
                data = data.decode()
                self.recv(data, addr)  # 保存信息到队列
        # 出错后不中断，处理异常，继续执行except:后的代码
        except:
            print(user + ' Connection lose')
            self.delUsers(conn, addr)  # 将断开用户移出users
            conn.close()

    # 判断断开用户在users中是第几位并移出列表, 刷新客户端的在线用户显示
    def delUsers(self, conn, addr):
        a = 0
        for user in users:  # 循环遍历users
            if user[0] == conn:
                users.pop(a)
                print(' Remaining online users: ', end='')  # 打印剩余在线用户(conn)
                d = onlines()
                self.recv(d, addr)
                print(d)
                break
            a += 1

    # 将接收到的信息(ip,端口以及发送的信息)存入que队列
    # 由于多个tcp连接可能会不断地对全局que进行修改,需要设置lock
    def recv(self, data, addr):
        lock.acquire()
        try:
            que.put((addr, data))
        # 无论是否出现异常最后均执行
        finally:
            lock.release()  # try...finally... finally后的代码一定会被执行

    # 将队列que中的消息发送给所有连接到的用户
    # 独立线程，队列中有消息就发送
    def sendData(self):
        while True:
            if not que.empty():
                data = ''
                message = que.get()  # 取出队列第一个元素并将其删除
                # message[0]是addr,message[1]是data
                if isinstance(message[1], str):  # 如果data是str则返回Ture, isinstance()判断两种类型是否相同
                    for i in range(len(users)):
                        # user[i][0]是socket连接,user[i][1]是用户名,users[i][2]是addr
                        for j in range(len(users)):
                            # 群发,寻找该条message是哪个user发送的,之后对所有在线的用户都发送一条信息,即user[i].send
                            if message[0] == users[j][2]:
                                print(' this: message is from user[{}]'.format(j))
                                data = ' ' + users[j][1] + ':' + message[1]
                                break
                        users[i][0].send(data.encode())
                if isinstance(message[1], list):  # 同上
                    # 如果是list则打包后直接发送
                    data = json.dumps(message[1])  # json.dumps()将列表类型数据进行json格式编码
                    for i in range(len(users)):
                        try:
                            users[i][0].send(data.encode())
                        except:
                            pass

    def run(self):
        # s.bind()绑定地址(host,port)到socket,以元组(host,port)的形式表示地址
        self.s.bind(self.ADDR)
        self.s.listen(5)
        print('Chat server starts running...')
        q = threading.Thread(target=self.sendData)
        # 启动一个线程用于发数据
        q.start()
        while True:
            # 每有一个host加入就开一个线程进行连接
            # s.accept() 阻塞式等待TCP客户端的连接，conn是新的socket对象
            conn, addr = self.s.accept()
            # target线程调用的对象，args: target调用的实参，元组格式
            t = threading.Thread(target=self.tcp_connect, args=(conn, addr))
            # start()方法启动子线程
            t.start()


################################################################
class FileServer(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.ADDR = ('', port)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.first = r'./resources'  # r去除转义字符
        os.chdir(self.first)  # 把first设为当前工作路径

    # self.conn = None

    def tcp_connect(self, conn, addr):
        print(' Connected by: ', addr)
        while True:
            data = conn.recv(1024)
            data = data.decode()
            if data == 'quit':
                print('Disconnected from {0}'.format(addr))
                break
            order = data.split(' ')[0]  # 获取动作   split(' ')[0] 得到空格之前的内容
            self.recv_func(order, data, conn)  # 判断输入的命令并执行对应的函数
        conn.close()

    # 传输当前目录列表
    def sendList(self, conn):
        listdir = os.listdir(os.getcwd())
        listdir = json.dumps(listdir)
        conn.sendall(listdir.encode())

    # 发送文件函数
    def sendFile(self, message, conn):
        name = message.split()[1]  # 获取第二个参数(文件名)
        fileName = r'./' + name
        size = os.path.getsize(fileName)
        print("发送 : ", name, "  (", size, "bytes)")

        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(('', 50001))
        sock.listen(3)
        connn, addr = sock.accept()
        dic = {"name": name, "file_size": size}
        connn.send(json.dumps(dic).encode())
        # connn.sendall(struct.pack('>I', size))
        # 不断地将文件进行拆分,分成多个部分进行发送
        new_size = size
        with open(fileName, 'rb') as f:
            while new_size:
                content = f.read(1024)
                connn.send(content)
                new_size -= len(content)
                print("\r已完成 : {:.0f}%".format((size - new_size) / size * 100), end="", flush=True)
            print('')
        print('传输结束EOF')
        connn.close()
        sock.close()

    # 保存上传的文件到当前工作目录
    def recvFile(self, message, conn):
        name = message.split()[1]  # 获取文件名
        fileName = r'./' + name
        data = conn.recv(2048)
        dic = json.loads(data.decode())

        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_path, dic.get('name'))
            if os.path.exists(file_path):
                file_seek = os.path.getsize(file_path)
            else:
                file_seek = 0
            # 将文件指针发送过去，同时也可以解决粘包
            conn.send(str(file_seek).encode())
            if file_seek == dic['file_size']:
                print('文件已经传输完成，退出此次传输...')
            else:
                # 重新设置需要接收的文件大小
                new_size = dic['file_size'] - file_seek
                print(new_size)
                # 准备接收发来的追加文件内容
                with open(file_path, 'ab') as f:
                    while new_size:
                        content = conn.recv(1024)
                        f.write(content)
                        new_size -= len(content)
                        # 因为Python中recv()是阻塞的，只有连接断开或异常时，接收到的是b''空字节类型，因此需要判断这种情况就断开连接。
                        if content == b'':
                            is_conn = False
                            break
            if not is_conn:
                print('有连接客户端断开...')

        except Exception as e:
            print('有连接出现异常断开：', str(e))


    # 切换工作目录
    def cd(self, message, conn):
        message = message.split()[1]  # 截取目录名
        # 如果是新连接或者下载上传文件后的发送则 不切换 只将当前工作目录发送过去
        if message != 'same':
            f = r'./' + message
            os.chdir(f)
        # path = ''
        path = os.getcwd().split('/')  # 当前工作目录
        i = 0
        for i in range(len(path)):
            if path[i] == 'resources':
                break
        pat = ''
        for j in range(i, len(path)):
            pat = pat + path[j] + ' '
        pat = '/'.join(pat.split())
        # 如果切换目录超出范围则退回切换前目录
        if 'resources' not in path:
            f = r'/root/exp/resources'
            os.chdir(f)
            pat = 'resources'
        conn.send(pat.encode())

    # 判断输入的命令并执行对应的函数
    def recv_func(self, order, message, conn):
        if order == 'get':
            return self.sendFile(message, conn)
        elif order == 'put':
            return self.recvFile(message, conn)
        elif order == 'dir':
            return self.sendList(conn)
        elif order == 'cd':
            return self.cd(message, conn)

    def run(self):
        print('File server starts running...')
        self.s.bind(self.ADDR)
        # 表示操作系统可以挂起的最大连接数量
        self.s.listen(3)
        while True:
            conn, addr = self.s.accept()  # 阻塞式的
            t = threading.Thread(target=self.tcp_connect, args=(conn, addr))
            t.start()


#############################################################################
class PictureServer(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        # self.setDaemon(True)
        self.ADDR = ('', port)
        # self.PORT = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.conn = None
        
        self.folder = './Server_image_cache/'  # 图片的保存文件夹 ./Client_image_cache/

    def tcp_connect(self, conn, addr):
        while True:
            data = conn.recv(1024)
            data = data.decode()
            print('Received message from {0}: {1}'.format(addr, data))
            if data == 'quit':
                break
            order = data.split()[0]  # 获取动作 get / put
            self.recv_func(order, data, conn)
        conn.close()
        print('---')

    # 发送文件函数, 向客户端发送，对应get动作
    def sendFile(self, message, conn):
        print(message)
        name = message.split()[1]  # 获取第二个参数(文件名)
        fileName = self.folder + name  # 将文件夹和图片名连接起来
        f = open(fileName, 'rb')
        while True:
            a = f.read(1024)
            if not a:
                break
            conn.send(a)
        time.sleep(0.1)  # 延时确保文件发送完整
        conn.send('EOF'.encode())
        print('Image sent!')

    # 保存上传的文件到当前工作目录
    def recvFile(self, message, conn):
        print(message)
        name = message.split(' ')[1]  # 获取文件名
        fileName = self.folder + name  # 将文件夹和图片名连接起来
        print(fileName)
        print('Start saving!')
        f = open(fileName, 'wb+')
        while True:
            data = conn.recv(1024)
            if data == 'EOF'.encode():
                print('Saving completed!')
                break
            f.write(data)

    # 判断输入的命令并执行对应的函数
    def recv_func(self, order, message, conn):
        if order == 'get':
            return self.sendFile(message, conn)
        elif order == 'put':
            return self.recvFile(message, conn)

    def run(self):
        self.s.bind(self.ADDR)
        self.s.listen(5)
        print('Picture server starts running...')
        while True:
            conn, addr = self.s.accept()
            t = threading.Thread(target=self.tcp_connect, args=(conn, addr))
            t.start()


####################################################################################
# 登录界面的验证接口
online_socket = list()  # 在线用户的连接列表，用于群发消息
socket2user = dict()  # 存储socket连接和用户名的对应关系


def encrypt_psw(str):
    """
    使用 MD5 算法对用户的密码进行加密
    :param str: 待加密的密码字符串
    :return: 加密后的密码字符串
    """
    hl = hashlib.md5()
    hl.update(str.encode("utf-8"))  # 必须编码后才能加密
    return hl.hexdigest()


def check_user(username, encrypted_psw):
    """
    检查用户登录时输入的用户名和密码是否正确
    :param username: 待检查的用户名
    :param encrypted_psw: 待检查的用户密码
    :return: 用户名和密码是否通过的结果，True和False
    """
    print("开始检查用户信息是否有误")
    with open("users.txt", "r") as users_file:
        users_data = users_file.read()
    users_list = users_data.split()
    for user in users_list:
        if user == username:
            # 获得对应用户名的密码在列表中的索引
            index = users_list.index(user) + 1
            if users_list[index] == encrypted_psw:
                return "登录成功！"
            else:
                return "密码输入有误，请重新输入！"
    else:
        return "不存在该用户，请先注册！"


def add_user(new_socket, username, encrypted_psw):
    """
    将要注册的用户名进行判断是否有重复用户名，
    如果没有，就将注册用户信息写入本地文本中
    :param new_socket: 本次连接的客户端的套接字
    :param username: 待注册的用户名
    :param encrypted_psw: 加密后的密码
    """
    try:
        print("register: user: " + username + ", key: " + encrypted_psw)

        # 读取本地用户文本，并分隔成一个字符串列表
        with open("users.txt", "r") as users_file:
            users_data = users_file.read()
        users_list = users_data.split("\n")

        # 遍历查询列表中是否已存在用户名
        for user in users_list:
            if user == username:  # 用户名已存在
                new_socket.sendall("抱歉，用户名已存在！".encode("utf-8"))
                return
        else:
            # 添加用户和用md5加密后的密码
            with open("users.txt", "a") as users_file:
                users_file.write(username + "\n" + encrypted_psw + "\n")
            new_socket.sendall("注册成功！".encode("utf-8"))
    except Exception as ret:
        print("添加用户数据出错：" + str(ret))
        new_socket.sendall("发生未知错误！".encode("utf-8"))


def handle_login(new_socket):
    """
    处理登录请求
    :param new_socket: 用户连接时生成的套接字
    """
    username_psw = new_socket.recv(1024).decode("utf-8")
    # 组装后的用户信息格式为 username#!#!password
    ret = re.search(r"(.+)#!#!(.+)", username_psw)
    username = ret.group(1)
    password = ret.group(2)
    encrypted_psw = encrypt_psw(password)
    check_result = check_user(username, encrypted_psw)
    new_socket.sendall(check_result.encode("utf-8"))  # 将登陆结果发送给客户端


def handle_reg(new_socket):
    """
    处理客户端的注册请求，接收客户端注册的用户信息，
    调用函数将用户名和加密后的密码存入本地文本
    :param new_socket: 本次连接过来的客户端套接字
    """
    username_psw = new_socket.recv(1024).decode("utf-8")
    # 组装后的用户格式为 username#!#!password
    ret = re.search(r"(.+)#!#!(.+)", username_psw)
    username = ret.group(1)
    password = ret.group(2)
    encrypted_psw = encrypt_psw(password)
    add_user(new_socket, username, encrypted_psw)


def login(new_socket, addr):
    try:
        while True:
            req_type = new_socket.recv(1).decode("utf-8")  # 获取请求类型
            print(req_type)
            if req_type:  # 如果不为真，则说明客户端已断开
                if req_type == "1":  # 登录请求
                    print("开始处理登录请求")
                    handle_login(new_socket)
                elif req_type == "2":  # 注册请求
                    print("开始处理注册请求")
                    handle_reg(new_socket)
            else:
                break
    except Exception as ret:
        print(str(addr) + " 连接异常，准备断开: " + str(ret))


class LoginServer(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.ADDR = ('', port)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        os.chdir(sys.path[0])

    def run(self):
        self.s.bind(self.ADDR)
        self.s.listen(5)
        print('login server begin')
        while True:
            conn, addr = self.s.accept()
            t = threading.Thread(target=login, args=(conn, addr))
            t.start()


##############################################################################
class P2Pfile(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.ADDR = ('', port)
        self.s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # SO_REUSEADDR立即释放端口
        self.judge = 1

    def tcp_connect(self):
        conn1, addr1 = self.s.accept()
        conn1_info = addr1[0] + '|' + str(addr1[1]) + '|0'
        conn1.sendall("#你已连接上,请等待另一名用户\n".encode())
        print(conn1_info)

        data = conn1.recv(1024)
        print(data.decode())

        conn2, addr2 = self.s.accept()
        conn2_info = addr2[0] + '|' + str(addr2[1]) + '|1'
        conn2.sendall("#你已连接上,另一名用户已就绪\n".encode())
        print(conn2_info)
        conn2.sendall(data)

        conn1.close()
        conn2.close()
        self.judge = 1

    def run(self):
        self.s.bind(self.ADDR)
        self.s.listen(5)
        print('P2P File server starts running...')
        while True:
            if self.judge:
                t = threading.Thread(target=self.tcp_connect)
                t.start()
                self.judge = 0


###################################################################################
class VoiceServer(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.ADDR = ('', port)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(self.ADDR)
        # 所有连接语音服务器的客户端socket连接
        self.connections = []
        # self.accept_connections()

    def run(self):
        print('voice server starts running...')
        self.s.listen(10)
        while True:
            conn, addr = self.s.accept()
            print('语音服务器连接上一个客户端')
            self.connections.append(conn)
            threading.Thread(target=self.handle_client, args=(conn, addr,)).start()

    def broadcast(self, conn, data):
        for client in self.connections:
            if client != self.s and client != conn:
                try:
                    client.send(data)
                except:
                    pass

    def delconnections(self, conn, addr):
        a = 0
        for user in self.connections:  # 循环遍历users
            if user == conn:
                self.connections.pop(a)
                break
            a += 1

    def handle_client(self, conn, addr):
        while True:
            try:
                data = conn.recv(1024)
                # 广播
                self.broadcast(conn, data)
            except socket.error:
                conn.close()
                self.delconnections(conn, addr)


####################################################################################
class P2PVoice(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ADDR = ('', port)
        self.judge = 1

    def tcp_connect(self):
        conn1, addr1 = self.sock.accept()
        conn1.sendall("#你已连接上,请等待另一名用户\n".encode())

        conn2, addr2 = self.sock.accept()
        conn2.sendall("#你已连接上,另一名用户已就绪\n".encode())

        conn1_info = addr1[0] + "|" + str(addr1[1]) + "|" + str(addr2[1])
        conn2_info = addr2[0] + "|" + str(addr2[1]) + "|" + str(addr1[1])

        conn1.sendall(conn2_info.encode())
        conn2.sendall(conn1_info.encode())
        conn1.close()
        conn2.close()

        self.judge = 1

    def run(self):
        self.sock.bind(self.ADDR)
        self.sock.listen(5)
        print('P2P Voice starts running...')
        while True:
            if self.judge:
                t = threading.Thread(target=self.tcp_connect)
                t.start()
                self.judge = 0


###################################################################################
if __name__ == '__main__':
    # 启动五个线程
    cserver = ChatServer(PORT)  # 50007 聊天端口
    fserver = FileServer(PORT + 1)  # 50008 文件端口
    loginserver = LoginServer(PORT + 3)  # 50010 登录端口
    p2pserver = P2Pfile(PORT + 4)  # 50011 p2p文件端口
    voiceserver = VoiceServer(PORT + 5)  # 50012 语音端口

    cserver.start()
    fserver.start()
    loginserver.start()
    p2pserver.start()
    voiceserver.start()

    while True:
        time.sleep(1)
        if not cserver.isAlive():
            print("Chat connection lost...")
            sys.exit(0)
        if not fserver.isAlive():
            print("File connection lost...")
            sys.exit(0)
        if not loginserver.isAlive():
            print("login over")
            sys.exit(0)
        if not p2pserver.isAlive():
            print("P2P connection lost...")
            sys.exit(0)
        if not voiceserver.isAlive():
            print("voice connection lost...")
            sys.exit(0)
