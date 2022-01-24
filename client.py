import socket
import threading
import json     # json.dumps(some)打包   json.loads(some)解包
from tkinter import *
import tkinter.messagebox
from tkinter.scrolledtext import ScrolledText  # 导入多行文本框用到的包
from tkinter import filedialog
from tkinter import messagebox
import os
import struct
from time import sleep
import pyaudio

# IP = ''
# PORT = ''
user = ''
listbox1 = ''  # 用于显示在线用户的列表框
ii = 0  # 用于判断是开还是关闭列表框
users = []  # 在线用户列表
chat = '------Group chat-------'  # 聊天对象, 默认为群聊

# destip = '127.0.0.1'
destip = '1.116.227.117' # 云服务器公网IP

class Client:
    """创建客户端的模板类"""
    def __init__(self):
        print("初始化tcp多人聊天室客户端")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((destip, 50010))

    def send_login_info(self, username, password):
        """
        发送登录用户的用户名和密码给服务器验证，并return验证结果
        :param username: 待验证的用户名
        :param password: 待验证的密码
        :return: 验证结果
        """
        # 告诉服务器本次请求的类型，“1” 是验证登录
        self.client_socket.sendall("1".encode("utf-8"))
        # 将用户名和密码按照一定规律组合后一起发送给服务器
        username_psw = username + "#!#!" + password
        self.client_socket.sendall(username_psw.encode("utf-8"))
        # 获取服务器的返回值，"1"代表通过，“0”代表不通过，再放回True or False
        check_result = self.client_socket.recv(1024).decode("utf-8")
        return check_result

    def send_register_info(self, username, password, confirm):
        """
        发送用户注册的用户名和密码给服务器，并返回注册结果
        :param username: 待注册的用户名
        :param password: 待注册的密码
        :param confirm: 确认密码
        :return: 注册结果
        """
        # 判断两次输入的密码是否一致
        if not password == confirm:
            return "密码不一致，请重新输入！"
        # 告诉服务器本次请求类型，“2” 是注册用户
        self.client_socket.sendall("2".encode("utf-8"))
        # 将用户名和密码按一定规律组装后发送给服务器
        username_psw = username + "#!#!" + password
        self.client_socket.sendall(username_psw.encode("utf-8"))
        # 获取服务器返回的结果
        check_result = self.client_socket.recv(1024).decode("utf-8")
        return check_result

    def send_msg(self, content):
        # 向服务器发送数据  content: 待发送的内容
        # 告诉服务器本次请求类型，“3” 是发送消息
        self.client_socket.sendall("3".encode("utf-8"))
        self.client_socket.sendall(content.encode("utf-8"))
    def recv_data(self, size=1024):
        # 客户端向服务器接收数据
        return self.client_socket.recv(size).decode("utf-8")
    def close(self):
        self.client_socket.close()

class LoginPanel:
    """登录界面模板类，只需另外传入其他对象的方法"""
    def __init__(self):
        self.login_frame = Tk()
        self.username = None
        self.password = None
    # 设置登陆界面在屏幕中的位置和大小
    def set_panel_position(self):
        screen_width = self.login_frame.winfo_screenwidth()  # 获取屏幕宽度
        screen_height = self.login_frame.winfo_screenheight()  # 获取屏幕高度
        width = 400
        height = 300
        gm_str = "%dx%d+%d+%d" % (width, height, (screen_width - width) / 2,
                                  (screen_height - 1.2 * height) / 2)
        self.login_frame.geometry(gm_str)
    # 给登陆界面设置其他配置
    def config_for_reg_panel(self):
        self.login_frame.configure(background="lightblue")
        self.login_frame.resizable(width=False, height=False)  # 设置界面大小可调
        self.login_frame.title("Login")
    # 放置界面标题
    def set_title(self):
        title_lable = Label(self.login_frame, text="MyChat - Login", font=("Microsoft Yahei", 16),
                            fg="black", bg="lightblue")
        title_lable.pack(ipady=10, fill=X)
    # 放置登陆表单
    def set_form(self):
        # 1、创建框架
        form_frame = Frame(self.login_frame, bg="lightblue")
        form_frame.pack(fill=X, padx=20, pady=10)

        # 2、添加用户名、密码标签，并设置字体、背景色、前景色并用grid布局
        Label(form_frame, text="username：", font=("Microsoft Yahei", 12), bg="lightblue", fg="black").grid(row=0,
                                                                                                           column=3,
                                                                                                           pady=20)
        Label(form_frame, text="password：", font=("Microsoft Yahei", 12), bg="lightblue", fg="black").grid(row=1,
                                                                                                           column=3,
                                                                                                           pady=20)

        # 3、设置输入框，储存用户输入的用户名和密码
        self.username = StringVar()
        self.password = StringVar()
        Entry(form_frame, textvariable=self.username, bg="#e3e3e3", width=30).grid(row=0, column=4, ipady=1)
        Entry(form_frame, textvariable=self.password, show="*", bg="#e3e3e3", width=30).grid(row=1, column=4, ipady=1)
    # 放置注册和登陆按钮
    def set_btn(self):
        btn_frame = Frame(self.login_frame, bg="lightblue")
        btn_reg = Button(btn_frame, text="Register", bg="lightblue", fg="black", width=15,
                         font=('Microsoft Yahei', 12), command=self.reg_func)
        btn_reg.pack(side=LEFT, ipady=3)

        btn_login = Button(btn_frame, text="Login", bg="lightblue", fg="black", width=15,
                           font=('Microsoft Yahei', 12), command=self.login_func)
        btn_login.pack(side=RIGHT, ipady=3)
        btn_frame.pack(fill=X, padx=20, pady=20)
    # 调用实例方法给登录界面做整体布局
    def show(self):
        self.set_panel_position()
        self.config_for_reg_panel()
        self.set_title()
        self.set_form()
        self.set_btn()
        self.login_frame.mainloop()

    # 实现对界面的关闭
    def close(self):
        # 先判断是否有界面
        if self.login_frame == None:
            print("未显示界面")
        else:
            self.login_frame.destroy()
    # 获取用户输入的用户名和密码
    def get_input(self):
        # return: 返回获得的用户名和密码
        return self.username.get(), self.password.get()
    # 封装到登陆界面中的登录按钮的功能。
    def login_func(self):
        global user
        username, password = self.get_input()
        client = Client()
        check_result = client.send_login_info(username, password)
        if check_result == "登录成功！":
            messagebox.showinfo(title="Success", message="登陆成功！")
            self.close()
            user = username
        elif check_result == "密码输入有误，请重新输入！":
            messagebox.showerror(title="Error", message="密码输入有误，请重新输入！")
        elif check_result == "不存在该用户，请先注册！":
            messagebox.showerror(title="Error", message="不存在该用户，请先注册！")
    # 封装到登录界面的注册按钮中，实现从登录界面跳转到注册界面
    def reg_func(self):
        self.close()
        reg_panel = RegPanel()
        reg_panel.show()

class RegPanel:
    # 注册界面模板类，只需另外传入其他对象的方法
    def __init__(self):
        self.reg_frame = Tk()
        self.username = None   # 注册的用户名
        self.password = None   # 密码
        self.confirm = None    # 验证密码
    # 设置注册界面在屏幕中的位置和大小
    def set_panel_position(self):
        screen_width = self.reg_frame.winfo_screenwidth()
        screen_height = self.reg_frame.winfo_screenheight()
        width = 400
        height = 360
        gm_str = "%dx%d+%d+%d" % (width, height, (screen_width - width) / 2, (screen_height - 1.2 * height) / 2)
        self.reg_frame.geometry(gm_str)
    # 给注册界面设置其他配置
    def config_for_reg_panel(self):
        self.reg_frame.configure(background="lightblue")
        # 设置窗口关闭按钮时，调用方法，用于退出时关闭socket连接
        self.reg_frame.protocol("WM_DELETE_WINDOW", self.close_callback)
        # 界面可调整大小
        self.reg_frame.resizable(width=False, height=False)
        self.reg_frame.title("Register")
    # 放置界面标题
    def set_title(self):
        title_lable = Label(self.reg_frame, text="MyChat - Register", font=("Microsoft Yahei", 16), fg="black",
                            bg="lightblue")
        title_lable.pack(ipady=10, fill=X)
    # 放置注册表单
    def set_form(self):
        form_frame = Frame(self.reg_frame, bg="lightblue")
        form_frame.pack(fill=X, padx=20, pady=10)

        # 设置用户名、密码标签
        Label(form_frame, text="username：", font=("Microsoft Yahei", 12), bg="lightblue", fg="black").grid(row=0,
                                                                                                           column=1,
                                                                                                           pady=20)
        Label(form_frame, text="password：", font=("Microsoft Yahei", 12), bg="lightblue", fg="black").grid(row=1,
                                                                                                           column=1,
                                                                                                           pady=20)
        Label(form_frame, text=" confirm：", font=("Microsoft Yahei", 12), bg="lightblue", fg="black").grid(row=2, column=1,
                                                                                                     pady=20)

        # 设置变量，存储用户名和密码
        self.username = StringVar()
        self.password = StringVar()
        self.confirm = StringVar()

        # 设置输入框
        Entry(form_frame, textvariable=self.username, bg="#e3e3e3", width=30).grid(row=0, column=2, ipady=1)
        Entry(form_frame, textvariable=self.password, show="*", bg="#e3e3e3", width=30) \
            .grid(row=1, column=2, ipady=1)
        Entry(form_frame, textvariable=self.confirm, show="*", bg="#e3e3e3", width=30) \
            .grid(row=2, column=2, ipady=1)
    # 放置取消和注册按钮
    def set_btn(self):
        btn_frame = Frame(self.reg_frame, bg="lightblue")
        btn_quit = Button(btn_frame, text="Cancel", bg="lightblue", fg="black", width=15,
                          font=('Microsoft Yahei', 12), command=self.quit_func)
        btn_quit.pack(side=LEFT, ipady=3)

        btn_reg = Button(btn_frame, text="Register", bg="lightblue", fg="black", width=15,
                         font=('Microsoft Yahei', 12), command=self.reg_func)
        btn_reg.pack(side=RIGHT, ipady=3)
        btn_frame.pack(fill=X, padx=20, pady=20)
    # 注册界面布局
    def show(self):
        self.set_panel_position()
        self.config_for_reg_panel()
        self.set_title()
        self.set_form()
        self.set_btn()

        # 启动注册界面，让其显示
        self.reg_frame.mainloop()
    def close(self):
        if self.reg_frame == None:
            print("未显示界面")
        else:
            self.reg_frame.destroy()
    # 获取输入的用户名、密码、确认密码
    def get_input(self):
        return self.username.get(), self.password.get(), self.confirm.get()
    # 封装到注册界面中的取消按钮中，实现从注册界面跳转到登陆界面
    def quit_func(self):
        self.close()
        login_panel = LoginPanel()
        login_panel.show()
    # 封装到注册界面的注册按钮中
    def reg_func(self):
        username, password, confirm = self.get_input()
        client = Client()
        ret = client.send_register_info(username, password, confirm)
        print(ret)
        if ret == "密码不一致，请重新输入！":
            messagebox.showerror(title="Error", message="密码不一致，请重新输入！")
        else:
            if ret == "抱歉，用户名已存在！":
                messagebox.showerror(title="Error", message="抱歉，用户名已存在！")
            elif ret == "注册成功！":
                # 注册成功后提示，然后跳回登录界面
                messagebox.showinfo(title="Success", message="注册成功！")
                self.close()
                login_panel = LoginPanel()
                login_panel.show()
            else:
                messagebox.showerror(title="Error", message="发生未知错误！")
    def close_callback(self):
        self.close()
        login_panel = LoginPanel()
        login_panel.show()

# 登录按钮
login_panel = LoginPanel()
login_panel.show()

IP = destip
PORT = 50007
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((IP, PORT))
if user:
    s.send(user.encode())  # 发送用户名
else:
    s.send('no'.encode())  # 没有输入用户名则标记no，保证和server端刚开始进行连接时所确定的信息相同

# 如果没有用户名则将ip和端口号设置为用户名
addr = s.getsockname()  # 获取客户端ip和端口号, 内网IP与端口
addr = addr[0] + ':' + str(addr[1])
print(addr)
if user == '':
    user = addr

# 聊天窗口
# 创建图形界面
root = tkinter.Tk()
root.title(user)  # 窗口命名为用户名
root['height'] = 400
root['width'] = 600
root.resizable(0, 0)  # 限制窗口大小

# 创建多行文本框
listbox = ScrolledText(root)
listbox.place(x=5, y=0, width=570, height=320)
# 文本框使用的字体颜色
listbox.tag_config('red', foreground='red')
listbox.tag_config('blue', foreground='blue')
listbox.tag_config('green', foreground='green')
listbox.insert(tkinter.END, 'Welcome to the chat room!', 'blue')

# 表情功能代码部分
# 四个按钮, 使用全局变量, 方便创建和销毁
b1 = ''
b2 = ''
b3 = ''
b4 = ''
# 将图片打开存入变量中
p1 = tkinter.PhotoImage(file='./emoji/facepalm.png')
p2 = tkinter.PhotoImage(file='./emoji/smirk.png')
p3 = tkinter.PhotoImage(file='./emoji/concerned.png')
p4 = tkinter.PhotoImage(file='./emoji/smart.png')
# 用字典将标记与表情图片一一对应, 用于后面接收标记判断表情贴图
dic = {'aa**': p1, 'bb**': p2, 'cc**': p3, 'dd**': p4}
ee = 0  # 判断表情面板开关的标志

# 发送表情图标记的函数, 在按钮点击事件中调用
# 参数是发的表情图标记, 发送后将按钮销毁
def mark(exp):
    global ee
    mes = exp + ':;' + user + ':;' + chat
    s.send(mes.encode())
    b1.destroy()
    b2.destroy()
    b3.destroy()
    b4.destroy()
    ee = 0

# 四个对应的函数
def bb1():
    mark('aa**')  # 发送表情包标记
def bb2():
    mark('bb**')
def bb3():
    mark('cc**')
def bb4():
    mark('dd**')

# emoji按钮的动作
def express():
    global b1, b2, b3, b4, ee
    if ee == 0:
        ee = 1
        # 此处主要是将发送表情包的动作传到服务器上
        b1 = tkinter.Button(root, command=bb1, image=p1,
                            relief=tkinter.FLAT, bd=0)
        b2 = tkinter.Button(root, command=bb2, image=p2,
                            relief=tkinter.FLAT, bd=0)
        b3 = tkinter.Button(root, command=bb3, image=p3,
                            relief=tkinter.FLAT, bd=0)
        b4 = tkinter.Button(root, command=bb4, image=p4,
                            relief=tkinter.FLAT, bd=0)

        b1.place(x=5, y=248)
        b2.place(x=75, y=248)
        b3.place(x=145, y=248)
        b4.place(x=215, y=248)
    else:
        ee = 0
        b1.destroy()
        b2.destroy()
        b3.destroy()
        b4.destroy()

# 创建表情按钮
eBut = tkinter.Button(root, text='emoji', command=express)
eBut.place(x=5, y=320, width=60, height=30)

# 文件功能代码部分
# 将在文件功能窗口用到的组件名都列出来, 方便重新打开时会对面板进行更新
list2 = ''  # 列表框
label = ''  # 显示路径的标签
upload = ''  # 上传按钮
close = ''  # 关闭按钮

def fileClient():
    PORT2 = 50008  # 聊天室的端口为50007
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP, PORT2))

    # 修改root窗口大小显示文件管理的组件
    root['height'] = 390
    root['width'] = 760

    # 创建列表框
    list2 = tkinter.Listbox(root)
    list2.place(x=580, y=25, width=175, height=325)

    # 将接收到的目录文件列表打印出来(dir), 显示在列表框中
    def recvList(enter, lu):
        s.send(enter.encode())
        data = s.recv(4096)
        data = json.loads(data.decode())
        list2.delete(0, tkinter.END)  # 清空列表框
        lu = lu.split('/')  # split() 返回分割后的字符串列表,默认为分割所有
        if len(lu) != 1:
            list2.insert(tkinter.END, 'Return to the previous dir')
            list2.itemconfig(0, fg='green')
        for i in range(len(data)):
            list2.insert(tkinter.END, ('' + data[i]))
            if '.' not in data[i]:
                list2.itemconfig(tkinter.END, fg='orange')
            else:
                list2.itemconfig(tkinter.END, fg='blue')
    # 创建标签显示服务端工作目录
    def lab():
        global label
        data = s.recv(1024)  # 接收目录
        lu = data.decode()
        try:
            label.destroy()
            label = tkinter.Label(root, text=lu)
            label.place(x=580, y=0, )
        except:
            label = tkinter.Label(root, text=lu)
            label.place(x=580, y=0, )
        recvList('dir', lu)

    # 进入指定目录(cd)
    def cd(message):
        s.send(message.encode())

    # 刚连接上服务端时进行一次面板刷新
    cd('cd same')
    lab()

    # 接收下载文件(get)
    def getthread(fileName,name):
        if fileName:
            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.connect((IP,50001))

            data = sock.recv(1024)
            dic = json.loads(data.decode())
            print("接收 : ", name, "  (", dic['file_size'], "bytes)")
            new_size = dic['file_size']
            with open(fileName, 'wb') as f:
                while new_size:
                    content = sock.recv(1024)
                    f.write(content)
                    new_size -= len(content)
                    print("\r已完成 : {:.0f}%".format((dic['file_size']-new_size) / dic['file_size'] * 100), end="", flush=True)
            tkinter.messagebox.showinfo(title='Message',message='Download completed!')
            print('传输完成')
            sock.close()
            cd('cd same')
            lab()

    def get(message):
        print(message)
        name = message.split(' ')
        print(name)
        name = name[1]  # 获取命令的第二个参数(文件名)
        # 选择对话框, 选择文件的保存路径
        fileName = tkinter.filedialog.asksaveasfilename(title='Save file to', initialfile=name)
        s.send(message.encode())
        r = threading.Thread(target=getthread, args=(fileName,name))
        r.start()

    # 创建用于绑定在列表框上的函数
    def run(*args):
        indexs = list2.curselection()
        index = indexs[0]
        content = list2.get(index)
        # 如果有一个 . 则为文件
        if '.' in content:
            content = 'get ' + content
            # threading.Thread(target=get,args=(content)).start()
            get(content)
            # cd('cd same')
        elif content == 'Return to the previous dir':
            content = 'cd ..'
            cd(content)
        else:
            content = 'cd ' + content
            cd(content)
        lab()  # 刷新显示页面

    # 在列表框上设置绑定事件
    list2.bind('<ButtonRelease-1>', run)

    # 上传客户端所在文件夹中指定的文件到服务端, 在函数中获取文件名, 不用传参数
    def put():
        # 选择上传文件
        fileName = tkinter.filedialog.askopenfilename(title='Select upload file')
        if fileName:
            name = fileName.split('/')[-1]
            message = 'put ' + name
            s.send(message.encode())
            file_size = os.path.getsize(fileName)  # 上传文件大小
            dic = {"name": name, "file_size": file_size}
            s.send(json.dumps(dic).encode())
            file_seek = int(s.recv(100).decode())
            if file_seek == file_size:
                print('文件已经存在服务端，退出此次传输...')
            else:
                new_size = file_size - file_seek
                # 服务端表示准备好接收文件了，开始循环发送文件
                print("发送 : ", name, "  (", file_size, "bytes)")
                with open(fileName, 'rb') as f:
                    f.seek(file_seek)
                    while new_size:
                        content = f.read(1024)
                        s.send(content)
                        new_size -= len(content)
                        print("\r已完成 : {:.0f}%".format((file_size - new_size) / file_size * 100), end="", flush=True)
                    print('')
                tkinter.messagebox.showinfo(title='Message',message='Upload completed!')
        cd('cd same')
        lab()  # 上传成功后刷新显示页面
    def putfile():
        r = threading.Thread(target=put)
        r.start()
    # 创建上传按钮, 并绑定上传文件功能
    upload = tkinter.Button(root, text='Upload file', command=putfile)
    upload.place(x=600, y=353, height=30, width=80)

    # 关闭文件管理器, 待完善
    def closeFile():
        root['height'] = 390
        root['width'] = 580
        # 关闭连接
        s.send('quit'.encode())
        s.close()

    # 创建关闭按钮
    close = tkinter.Button(root, text='Close', command=closeFile)
    close.place(x=685, y=353, height=30, width=70)


# 创建文件按钮
fBut = tkinter.Button(root, text='File', command=fileClient)
fBut.place(x=65, y=320, width=60, height=30)

# 创建多行文本框, 显示在线用户
listbox1 = tkinter.Listbox(root)
listbox1.place(x=445, y=0, width=130, height=320)


def users():
    global listbox1, ii
    if ii == 1:
        listbox1.place(x=445, y=0, width=130, height=320)
        ii = 0
    else:
        listbox1.place_forget()  # 隐藏控件
        ii = 1

# 查看在线用户按钮
button1 = tkinter.Button(root, text='Users online', command=users)
button1.place(x=485, y=320, width=90, height=30)

# 创建输入文本框和关联变量
a = tkinter.StringVar()
a.set('')
entry = tkinter.Entry(root, width=120, textvariable=a)
entry.place(x=5, y=350, width=570, height=40)

def send(*args):
    # 没有添加的话发送信息时会提示没有聊天对象
    users.append('------Group chat-------')
    print(chat)
    if chat not in users:
        tkinter.messagebox.showerror('Send error', message='There is nobody to talk to!')
        return
    if chat == user:
        tkinter.messagebox.showerror('Send error', message='Cannot talk with yourself in private!')
        return
    mes = entry.get() + ':;' + user + ':;' + chat  # 添加聊天对象标记
    s.send(mes.encode())
    a.set('')  # 发送后清空文本框

# 创建send按钮
button = tkinter.Button(root, text='Send', command=send)
button.place(x=515, y=353, width=60, height=30)
root.bind('<Return>', send)  # 绑定回车发送信息

# 私聊功能
def private(*args):
    global chat
    # 获取点击的索引然后得到内容(用户名)
    indexs = listbox1.curselection()
    index = indexs[0]
    if index > 0:
        chat = listbox1.get(index)
        # 修改客户端名称
        if chat == '------Group chat-------':
            root.title(user)
            return
        ti = user + '  -->  ' + chat
        root.title(ti)

# 在显示用户列表框上设置绑定事件
listbox1.bind('<ButtonRelease-1>', private)

# 用于时刻接收服务端发送的信息并打印
def recv():
    global users
    while True:
        data = s.recv(1024)
        data = data.decode()
        try:  # 没有捕获到异常则表示接收到的是在线用户列表
            data = json.loads(data)  # 将json格式解压成列表类型
            users = data
            listbox1.delete(0, tkinter.END)  # 清空列表框
            number = ('   Users online: ' + str(len(data)))
            listbox1.insert(tkinter.END, number)
            listbox1.itemconfig(tkinter.END, fg='green', bg="#f0f0ff")
            listbox1.insert(tkinter.END, '------Group chat-------')
            listbox1.itemconfig(tkinter.END, fg='green')
            for i in range(len(data)):
                listbox1.insert(tkinter.END, (data[i]))
                listbox1.itemconfig(tkinter.END, fg='green')
        except:
            data = data.split(':;')
            data1 = data[0].strip()  # 消息
            data2 = data[1]  # 发送信息的用户名
            data3 = data[2]  # 聊天对象
            markk = data1.split(':')[1]
            # 判断是不是表情
            if (markk in dic):
                data4 = '\n' + data2 + '：'  # 例:名字-> \n名字：
                if data3 == '------Group chat-------':
                    if data2 == user:  # 如果是自己则将则字体变为蓝色
                        listbox.insert(tkinter.END, data4, 'blue')
                    else:
                        listbox.insert(tkinter.END, data4, 'green')  # END将信息加在最后一行
                elif data2 == user or data3 == user:  # 显示私聊
                    listbox.insert(tkinter.END, data4, 'red')  # END将信息加在最后一行
                
                listbox.image_create(tkinter.END, image=dic[markk])
            else:
                data1 = '\n' + data1
                if data3 == '------Group chat-------':
                    if data2 == user:  # 如果是自己则将则字体变为蓝色
                        listbox.insert(tkinter.END, data1, 'blue')
                    else:
                        listbox.insert(tkinter.END, data1, 'green')  # END将信息加在最后一行

                elif data2 == user or data3 == user:  # 显示私聊
                    listbox.insert(tkinter.END, data1, 'red')  # END将信息加在最后一行
            listbox.see(tkinter.END)  # 显示在最后

###################################################################
def p2pfilePut(fileName):
    server_address=IP
    server_port=PORT + 4
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    local_port = 33000  # 本地端口

    sock.connect((server_address, server_port))

    rcv_msgs = sock.recv(1024).decode()
    print(rcv_msgs)

    addr = sock.getsockname()  # 获取客户端ip和端口号
    sock_info = addr[0] + '|'+ str(local_port)
    sock.sendall(sock_info.encode())
    sock.close()

    recv_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    ADDR = (addr[0], local_port)
    print(ADDR)
    recv_sock.bind(ADDR)
    recv_sock.listen(5)
    conn, addr = recv_sock.accept()

    conn.sendall(os.path.split(fileName)[1].encode())  # 发送文件名
    size = os.path.getsize(fileName)
    print("共发送", size, "字节")
    conn.sendall(struct.pack(">I", size))  # 发送文件大小

    sleep(1)
    with open(fileName, "rb") as f:
        count = 0
        data = f.read(1024)
        while data:
            conn.sendall(data)
            count = count + len(data)
            print("\r已完成 : {:.0f}%".format(count / size * 100), end="", flush=True)
            data = f.read(1024)
        conn.sendall("".encode())
    conn.close()
    recv_sock.close()


def p2pfileGet():
    server_address = IP
    server_port = PORT + 4
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((server_address, server_port))
    rcv_msgs = sock.recv(1024).decode()
    while rcv_msgs.startswith("#"):
        print(rcv_msgs)
        rcv_msgs = sock.recv(1024).decode()
    rcv_msgs = rcv_msgs.split("|")
    remote_addr = rcv_msgs[0]  # 另一个客户端IP地址
    remote_port = int(rcv_msgs[1])
    print(rcv_msgs)
    sock.close()

    conn = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

    while conn.connect_ex((remote_addr, remote_port)) != 0:  # 注意网络情况，可能为死循环
        sleep(1)
    print('连接成功')
    file_name = conn.recv(1024).decode()  # 接收文件名
#    filepath = tkinter.filedialog.asksaveasfilename(title='Save file to', initialfile=file_name)
    filepath =''
    size = struct.unpack(">I", conn.recv(1024))[0]  # 接收文件大小
    print("接收 : ", file_name, "  (", size, "bytes)")
    with open(os.path.join(filepath, file_name), "wb") as f:
        count = 0
        data = conn.recv(1024)
        print("\r已完成 : {:.0f}%".format(count / size * 100), end="", flush=True)
        while data:
            f.write(data)
            length = len(data)
            count += length
            print("\r已完成 : {:.0f}%".format(count / size * 100), end="", flush=True)
            data = conn.recv(1024)
    print(" 传输完成")
    conn.close()

def p2pput():
    fileName = tkinter.filedialog.askopenfilename(title='Select send file')
    # 如果有选择文件才继续执行
    if fileName:
        p2pfilePut(fileName)
p2psend = tkinter.Button(root, text='send', command=p2pput)
p2psend.place(x=125, y=320, width=60, height=30)

p2preceive = tkinter.Button(root, text='receive', command=p2pfileGet)
p2preceive.place(x=185, y=320, width=60, height=30)

##################################################################
# cs架构的语音聊天
class voicechat:
    def __init__(self):
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = 50012
        while True:
            try:
                self.ss.connect((IP, self.port))
                print("Connected to Server")
                break
            except:
                print("Couldn't connect to server")

        chunk_size = 1024  # 512
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 20000
        self.p = pyaudio.PyAudio()
        self.playing_stream = self.p.open(format=audio_format, channels=channels, rate=rate, output=True,
                                              frames_per_buffer=chunk_size)
        self.recording_stream = self.p.open(format=audio_format, channels=channels, rate=rate, input=True,
                                                frames_per_buffer=chunk_size)
        # start threads
        threading.Thread(target=self.receive_server_data).start()
        threading.Thread(target=self.send_data_to_server).start()

    def receive_server_data(self):
        while True:
            try:
                data = self.ss.recv(1024)
                self.playing_stream.write(data)
            except:
                pass

    def send_data_to_server(self):
        while True:
            try:
                data = self.recording_stream.read(1024)
                self.ss.send(data)
            except:
                pass

eBut = tkinter.Button(root, text='voice', command=voicechat)
eBut.place(x=245, y=320, width=60, height=30)
##################################################################
r = threading.Thread(target=recv)
r.start()  # 开始线程接收信息

root.mainloop()
s.close()  # 关闭图形界面后关闭TCP连接
