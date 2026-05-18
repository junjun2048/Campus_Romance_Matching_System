import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from ElGamal import *
from sm3 import *
import math
import os
import  sm4

class ChatClientGUI:
    """聊天客户端图形界面类"""
    def __init__(self, root, host='localhost', port=8888):
        self.root = root
        self.root.title("网恋配对系统")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.auth_lock = threading.Lock()
        self.font = ('SimHei', 10)
        self.host = host
        self.port = port
        self.client = ChatClient(host, port, self)

        self.elgamal = ElGamal()
        self.server_public_key = None
        self.client_private_key = None
        self.client_public_key = None

        self.create_ui()
        self.client_thread = threading.Thread(target=self.client.start)
        self.client_thread.daemon = True
        self.client_thread.start()
        self.auth_window = None  # 认证窗口
        self.info_dialog = None  #
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.info_dialog = None
        self.info_request = False
        self.pubkey_exchanged = False  # 新增：公钥交换状态

    def create_ui(self):
        # 创建美观的用户界面
        # 设置主窗口样式
        self.root.configure(bg='#f5f7fa')
        # 创建主框架
        self.main_frame = tk.Frame(self.root, bg='#f5f7fa', padx=15, pady=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        # 标题栏
        self.title_frame = tk.Frame(self.main_frame, bg='#f5f7fa')
        self.title_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Label(
            self.title_frame,
            text="来寻找你的有缘人吧！有缘人终成眷属",
            font=('Microsoft YaHei', 14, 'bold'),
            bg='#f5f7fa',
            fg='#2c3e50'
        ).pack(side=tk.LEFT)
        # 底部按钮框架 - 先放置按钮框架，确保它不会被其他组件覆盖
        self.button_frame = tk.Frame(self.main_frame, bg='#f5f7fa', height=60)
        self.button_frame.pack(fill=tk.X, pady=(10, 10), side=tk.BOTTOM)
        self.button_frame.pack_propagate(False)  # 防止框架收缩以适应内容
        # 匹配按钮
        self.match_button = tk.Button(
            self.button_frame,
            text="匹配",
            font=('Microsoft YaHei', 10, 'bold'),
            bg='#2ecc71',  # 绿色
            fg='white',
            activebackground='#27ae60',
            activeforeground='white',
            bd=0,
            relief=tk.RAISED,
            padx=100,
            pady=80,
            cursor='hand2',
            command=self.request_match
        )
        self.match_button.pack(side=tk.LEFT, padx=100, pady=10)
        # 退出按钮
        self.exit_button = tk.Button(
            self.button_frame,
            text="退出",
            font=('Microsoft YaHei', 10, 'bold'),
            bg='#e74c3c',  # 红色
            fg='white',
            activebackground='#c0392b',
            activeforeground='white',
            bd=0,
            relief=tk.RAISED,
            padx=100,
            pady=80,
            cursor='hand2',
            command=self.on_closing
        )
        self.exit_button.pack(side=tk.LEFT, padx=10, pady=10)
        # 聊天历史区域
        self.chat_history = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.WORD,
            font=('Microsoft YaHei', 11),
            bg='#ffffff',
            fg='#34495e',
            padx=15,
            pady=15,
            bd=0,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground='#d6deeb',
            highlightcolor='#5c9eff',
            insertbackground='#5c9eff',
            selectbackground='#e1eaf9',
            selectforeground='#34495e'
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.chat_history.config(state=tk.DISABLED)
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("未连接")
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.FLAT,
            anchor=tk.W,
            font=('Microsoft YaHei', 9),
            background='#e9edf4',
            foreground='#7f8c8d',
            padding=(10, 5)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        # 添加分割线
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(side=tk.BOTTOM, fill=tk.X)
        # 窗口居中
        self.center_window()

    def request_match(self):
        """处理匹配按钮点击事件"""
        if self.client.authenticated:
            self.client.send_user_message("PUSH_REQUEST")
            self.append_message("正在寻找匹配...")
        else:
            messagebox.showwarning("未登录", "请先登录后再进行匹配")

    def center_window(self, window=None):
        """使指定窗口在屏幕中居中显示（默认为主窗口）"""
        # 若未指定窗口，则默认使用主窗口（self.root）
        if window is None:
            window = self.root
        # 更新窗口状态以获取准确尺寸
        window.update_idletasks()
        # 获取窗口当前宽度和高度
        width = window.winfo_width()
        height = window.winfo_height()
        # 获取屏幕的宽度和高度
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        # 计算窗口居中的X和Y坐标（屏幕中心减去窗口一半尺寸）
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        # 设置窗口几何位置
        window.geometry(f'{width}x{height}+{x}+{y}')

    def append_message(self, message):
        """向聊天区域添加消息"""
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, message + "\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)

    def show_auth_window(self, return_to_choice=False, register=False):
        """显示认证窗口"""
        if hasattr(self, 'auth_window') and self.auth_window and self.auth_window.winfo_exists():
            self.auth_window.destroy()
        self.auth_window = tk.Toplevel(self.root)
        self.auth_window.title("用户认证" if not register else "用户注册")
        self.auth_window.geometry("350x300")
        self.auth_window.resizable(False, False)
        self.auth_window.configure(bg='#f0f0f0')
        self.auth_window.transient(self.root)
        self.auth_window.grab_set()
        frame = tk.Frame(self.auth_window, bg='#f0f0f0', padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title = tk.Label(
            frame,
            text="用户登录" if not register else "用户注册",
            font=('Microsoft YaHei', 12, 'bold'),
            bg='#f0f0f0',
            fg='#333333'
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        if register:
            # 注册界面
            tk.Label(frame, text="新用户名:", font=('Microsoft YaHei', 10), bg='#f0f0f0').grid(row=1, column=0,
                                                                                               sticky=tk.W, pady=5)
            self.username_entry = self.create_styled_entry(frame)
            self.username_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)

            tk.Label(frame, text="密码:", font=('Microsoft YaHei', 10), bg='#f0f0f0').grid(row=2, column=0, sticky=tk.W,
                                                                                           pady=5)
            self.password_entry = self.create_styled_entry(frame, show="*")
            self.password_entry.grid(row=2, column=1, sticky=tk.EW, pady=5)

            # 按钮样式
            btn_style = {
                'font': ('Microsoft YaHei', 10),
                'bg': '#4a90e2',
                'fg': 'white',
                'activebackground': '#3a7bc8',
                'activeforeground': 'white',
                'bd': 0,
                'padx': 10,
                'pady': 5
            }

            tk.Button(frame, text="注册", **btn_style, command=self.handle_register).grid(
                row=3, column=0, columnspan=2, pady=10, sticky=tk.EW
            )
            tk.Button(frame, text="返回登录", **btn_style, command=self.switch_to_login).grid(
                row=4, column=0, columnspan=2, pady=5, sticky=tk.EW
            )
        else:
            # 登录界面
            tk.Label(frame, text="用户名:", font=('Microsoft YaHei', 10), bg='#f0f0f0').grid(row=1, column=0,
                                                                                             sticky=tk.W, pady=5)
            self.username_entry = self.create_styled_entry(frame)
            self.username_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)

            tk.Label(frame, text="密码:", font=('Microsoft YaHei', 10), bg='#f0f0f0').grid(row=2, column=0, sticky=tk.W,
                                                                                           pady=5)
            self.password_entry = self.create_styled_entry(frame, show="*")
            self.password_entry.grid(row=2, column=1, sticky=tk.EW, pady=5)

            # 按钮样式
            btn_style = {
                'font': ('Microsoft YaHei', 10),
                'bg': '#4a90e2',
                'fg': 'white',
                'activebackground': '#3a7bc8',
                'activeforeground': 'white',
                'bd': 0,
                'padx': 10,
                'pady': 5
            }

            tk.Button(frame, text="登录", **btn_style, command=self.handle_login).grid(
                row=3, column=0, columnspan=2, pady=10, sticky=tk.EW
            )
            tk.Button(frame, text="注册账号", **btn_style, command=self.switch_to_register).grid(
                row=4, column=0, columnspan=2, pady=5, sticky=tk.EW
            )

        self.username_entry.focus_set()
        frame.columnconfigure(1, weight=1)
        self.auth_result = None
        # 确保窗口完全渲染后再居中
        self.auth_window.update_idletasks()
        self.center_window(self.auth_window)  # 传入认证窗口作为参数

    def create_styled_entry(self, parent, **kwargs):
        """创建统一风格的输入框"""
        return tk.Entry(
            parent,
            font=('Microsoft YaHei', 10),
            bg='white',
            fg='#333333',
            bd=0,
            highlightthickness=1,
            highlightbackground='#cccccc',
            highlightcolor='#4a90e2',
            insertbackground='#333333',
            **kwargs
        )

    def switch_to_login(self):
        """切换到登录界面"""
        self.show_auth_window(register=False)

    def switch_to_register(self):
        """切换到注册界面"""
        self.show_auth_window(register=True)

    def handle_login(self):
        """处理用户登录请求"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        for widget in self.auth_window.winfo_children():
            for item in widget.winfo_children():
                item.config(state=tk.DISABLED)
        self.auth_window.title("正在登录...")
        self.client.username=username
        hashed_password = generate_sm3_hash(password)
        self.client.send_auth_message("AUTH", username, hashed_password)

    def handle_register(self):
        """处理用户注册请求"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        for widget in self.auth_window.winfo_children():
            for item in widget.winfo_children():
                item.config(state=tk.DISABLED)
        self.auth_window.title("正在注册...")
        self.client.username = username

        # 对密码进行SM3哈希处理
        hashed_password = generate_sm3_hash(password)
        self.client.send_auth_message("REGISTER", username, hashed_password)

    def handle_user_info_request(self):
        """处理服务器的用户信息请求"""
        self.info_request = True
        if not self.info_dialog or not self.info_dialog.winfo_exists():
            self.create_info_dialog()
        else:
            self.info_dialog.deiconify()
            self.info_dialog.lift()

    def create_info_dialog(self):
        # 创建对话框
        self.info_dialog = tk.Toplevel(self.root)
        self.info_dialog.title("用户信息")
        self.info_dialog.geometry("400x320")  # 稍微放大一点
        self.info_dialog.resizable(False, False)
        self.info_dialog.transient(self.root)
        self.info_dialog.grab_set()
        # 居中显示
        self.center_window(self.info_dialog)
        # 使用ttk样式美化
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('微软雅黑', 10))
        style.configure('TButton', font=('微软雅黑', 10), padding=5)
        style.configure('TEntry', font=('微软雅黑', 10), padding=5)

        # 主框架
        main_frame = ttk.Frame(self.info_dialog, padding=(20, 15))
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题标签
        title_label = ttk.Label(
            main_frame,
            text="用户信息注册",
            font=('微软雅黑', 12, 'bold'),
            foreground='#2c3e50'
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        # 输入字段框架
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=2, column=0, columnspan=2, sticky='ew')

        # 姓名输入
        ttk.Label(input_frame, text="姓名:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.name_entry = ttk.Entry(input_frame)
        self.name_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)

        # 年龄输入
        ttk.Label(input_frame, text="年龄:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.age_entry = ttk.Entry(input_frame)
        self.age_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)

        # 性别输入
        ttk.Label(input_frame, text="性别:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        gender_frame = ttk.Frame(input_frame)
        self.gender_var = tk.StringVar(value="男")
        ttk.Radiobutton(
            gender_frame,
            text="男",
            variable=self.gender_var,
            value="男"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            gender_frame,
            text="女",
            variable=self.gender_var,
            value="女"
        ).pack(side=tk.LEFT, padx=5)
        gender_frame.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # 爱好输入
        ttk.Label(input_frame, text="爱好:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.hobby_entry = ttk.Entry(input_frame)
        self.hobby_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        ttk.Label(input_frame, text="电话号码:").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        self.phone_number = ttk.Entry(input_frame)
        self.phone_number.grid(row=4, column=1, sticky='ew', padx=5, pady=5)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(15, 0))

        # 提交按钮
        submit_btn = ttk.Button(
            button_frame,
            text="提交",
            command=self.submit_user_info,
        )
        submit_btn.pack(side=tk.RIGHT, padx=5)

        # 取消按钮
        cancel_btn = ttk.Button(
            button_frame,
            text="取消",
            command=self.info_dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        # 配置网格权重
        input_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # 设置焦点
        self.name_entry.focus_set()

        # 自定义按钮样式
        style.configure('Accent.TButton', foreground='white', background='#3498db')
        style.map('Accent.TButton',
                  background=[('active', '#2980b9'), ('pressed', '#2980b9')])

    def submit_user_info(self):
        """提交用户信息"""
        name = self.name_entry.get().strip()
        age = self.age_entry.get().strip()
        gender = self.gender_var.get()
        hobby = self.hobby_entry.get().strip()
        self.client.phone_number = self.phone_number.get().strip()
        if not name or not age or not gender or not hobby or not self.client.phone_number:
            messagebox.showerror("错误", "所有字段均为必填项")
            return
        try:
            age = int(age)
            if age <= 0 or age > 150 or not str(self.client.phone_number).isdigit() or not 3 <= len(str(self.client.phone_number)) <= 15:
                raise ValueError("年龄或者电话号码必须在合理范围内")
        except ValueError:
            messagebox.showerror("错误", "年龄或电话号码必须是有效数字")
            return
        key=sm4.generate_key()  # 生成SM4密钥
        phone=sm4.sm4_encrypt(key,self.client.phone_number)  # 加密电话号码
        file_name=f"{self.client.username}_phone_key.txt"
        key=int.from_bytes(key, byteorder='big', signed=False)  # 将SM4密钥转换成整数
        with open(file_name,"w")as f:  # 保存SM4密钥
            f.write(str(key))
        # 构建用户信息字符串
        user_info = f"{name},{age},{gender},{hobby},{phone}"
        self.client.send_user_message(f"USER_INFO:{user_info}")
        self.append_message(f"已提交用户信息: {name}, {age}, {gender}, {hobby},{self.client.phone_number}")
        self.info_dialog.destroy()
        self.info_request = False

    def handle_info_message(self, message):
        """处理服务器消息"""
        if message.startswith("USER_INFO_REQUEST:"):
            self.root.after(0, lambda: self.handle_user_info_request())
        elif message.startswith("USER_INFO_SAVED"):
            result = message[13:].strip()
            self.root.after(0, lambda: messagebox.showinfo("成功", result))
            # 信息保存成功后，客户端准备发送公钥
        elif message.startswith("USER_INFO_ERROR:"):
            error = message[13:].strip()
            self.root.after(0, lambda: messagebox.showerror("错误", error))
        elif message.startswith("NO_PUBLIC_KEY"):
            # 服务器请求客户端公钥
            self.generate_and_send_public_key()
        elif message.startswith("PUBLIC_KEY_RECEIVED"):
            self.pubkey_exchanged = True
            self.status_var.set(f"已认证: {self.client.username}，加密功能已启用")
            self.append_message("公钥交换完成")

        else:
            self.append_message(f"收到消息: {message}")

    def generate_and_send_public_key(self):
        """生成客户端密钥对并发送公钥"""
        try:
            if not self.server_public_key:
                raise ValueError("服务器公钥未设置")
            p, g, h, q = self.server_public_key  # 从服务器公钥中提取p和g
            # 尝试从文件加载私钥，如果不存在则生成新的
            private_key_file = f"{self.client.username}_private_key.txt"
            if os.path.exists(private_key_file):
                try:
                    with open(private_key_file, 'r') as f:
                        self.client_private_key = int(f.read().strip())
                    self.append_message(f"已从文件加载私钥")
                except:
                    self.client_private_key = self.elgamal.generate_private_key(q)  # 使用q生成私钥
                    self.save_private_key()
                    self.append_message(f"私钥文件损坏，已生成新私钥")
            else:
                self.client_private_key = self.elgamal.generate_private_key(q)  # 使用q生成私钥
                self.save_private_key()
                self.append_message(f"已生成新的私钥并保存")

            # 计算公钥: g^x mod p
            self.client_public_key = self.elgamal.generate_public_key(self.client_private_key, g, p)
            # 发送客户端公钥到服务器
            pubkey_msg = f"CLIENT_PUBKEY:{self.client_public_key}"
            self.client.send_user_message(pubkey_msg)
            self.append_message(f"已生成用户密钥对，公钥已发送")
        except Exception as e:
            self.append_message(f"生成/发送公钥失败: {str(e)}")

    def handle_public_key(self, public_key_tuple):
        """处理服务器公钥"""
        try:
            p, g, h, q = public_key_tuple
            self.server_public_key = (p, g, h, q)
            self.generate_and_send_public_key()
        except Exception as e:
            self.append_message(f"处理公钥失败: {str(e)}")

    def save_private_key(self):
        """保存私钥到本地文件"""
        if not self.client.username or self.client_private_key is None:
            return

        private_key_file = f"{self.client.username}_private_key.txt"
        try:
            with open(private_key_file, 'w') as f:
                f.write(str(self.client_private_key))
            self.append_message(f"私钥已保存到 {private_key_file}")
        except Exception as e:
            self.append_message(f"保存私钥失败: {str(e)}")

    def set_auth_result(self, result):
        """设置认证结果"""
        with self.auth_lock:
            self.auth_result = result
            self.root.after(0, self.process_auth_result)

    def process_auth_result(self):
        """处理认证结果"""
        if self.auth_result == "AUTH_SUCCESS":
            if self.auth_window:
                self.auth_window.destroy()
            self.exit_button.config(state=tk.NORMAL)
            self.match_button.config(state=tk.NORMAL)
        elif self.auth_result == "REGISTER_SUCCESS":
            messagebox.showinfo("成功", "注册成功! 请重新登录。")
            if self.auth_window:
                self.auth_window.destroy()
            self.show_auth_window()
        elif self.auth_result:
            messagebox.showerror("错误", self.auth_result)
            if self.auth_window:
                for widget in self.auth_window.winfo_children():
                    for item in widget.winfo_children():
                        item.config(state=tk.NORMAL)
                self.auth_window.title("用户认证")
        else:
            messagebox.showerror("错误", "认证超时，请重试")
            if self.auth_window:
                self.auth_window.destroy()
            self.show_auth_window()

    def handle_pair_key_message(self, message):
        temp = message.split()
        # 提取配对密钥
        pair_key = int(temp[0].split(':')[1])
        # 提取ElGamal加密所需的参数
        p = int(temp[1].split(':')[1])
        q = int(temp[2].split(':')[1])
        g = int(temp[3].split(':')[1])
        # 提取配对用户的信息
        pair_name = temp[4].split(':')[1]
        pair_gender = temp[5].split(':')[1]
        pair_age = temp[6].split(':')[1]
        pair_hobby = temp[7].split(':')[1]
        # 读取本地私钥文件
        private_key_file_name = f"{self.client.username}_private_key.txt"
        with open(private_key_file_name, "r") as f:
            private_key = int(f.readline())
        # 使用ElGamal算法计算共享密钥
        k = pow(pair_key, private_key, p)
        # 通过密钥派生函数生成最终的共享密钥
        share_private_key = derive_elgamal_private_key(k, q)  # 密钥派生

        # 将共享密钥与配对用户名关联并保存到文件
        share_key_file_name = f"{self.client.username}_share_key.txt"
        ms = f"{pair_name}:" + str(share_private_key) + "\n"
        with open(share_key_file_name, "a") as f1:
            f1.write(ms)
        # 在UI线程中显示配对用户信息和共享密钥
        self.root.after(0, lambda: self.show_pair_info_window(
            pair_name, pair_age, pair_gender, pair_hobby,
            share_private_key, p, g, q
        ))

    def show_pair_info_window(self, name, age, gender, hobby, share_key, p, g, q):
        """显示配对用户信息的窗口"""
        # 创建新窗口
        pair_window = tk.Toplevel(self.root)
        pair_window.title("配对结果")
        pair_window.geometry("400x450")
        pair_window.resizable(False, False)
        pair_window.transient(self.root)  # 设置为主窗口的子窗口
        pair_window.grab_set()  # 模态窗口，阻止操作主窗口

        # 配置浪漫主题颜色 - 调整按钮颜色使其更深且文字更清晰
        love_colors = {
            'bg': '#FFF0F5',  # 浅粉色背景
            'title': '#C71585',  # 深粉色标题
            'text': '#8B0000',  # 深红色文本
            'button': '#C71585',  # 更深的粉色按钮
            'button_text': '#FFFFFF',  # 按钮文本
            'button_pressed': '#800080',  # 按钮按下状态颜色
        }
        # 设置中文字体
        font = ('SimHei', 11)
        title_font = ('SimHei', 16, 'bold')
        subtitle_font = ('SimHei', 13, 'bold')
        # 创建Canvas背景
        canvas = tk.Canvas(pair_window, bg=love_colors['bg'], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        # 绘制装饰心形
        self._draw_decorative_hearts(canvas)
        # 创建半透明内容框架
        frame = ttk.Frame(canvas, style='Love.TFrame')
        frame.place(relx=0.5, rely=0.5, relwidth=0.85, relheight=0.85, anchor='center')
        # 标题
        title_label = ttk.Label(frame, text="💘 配对成功！ 💘", font=title_font,
                                foreground=love_colors['title'], style='Love.TLabel')
        title_label.pack(pady=(20, 15))
        # 添加标题动画效果
        self._animate_title(title_label)
        # 创建信息框架
        info_frame = ttk.Frame(frame, style='Love.TFrame')
        info_frame.pack(fill=tk.X, padx=20)
        # 姓名
        ttk.Label(info_frame, text="姓名:", font=font,
                  foreground=love_colors['text'], style='Love.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=8
        )
        ttk.Label(info_frame, text=name, font=font,
                  foreground=love_colors['text'], style='Love.TLabel').grid(
            row=0, column=1, sticky=tk.W, pady=8
        )
        # 年龄
        ttk.Label(info_frame, text="年龄:", font=font,
                  foreground=love_colors['text'], style='Love.TLabel').grid(
            row=1, column=0, sticky=tk.W, pady=8
        )
        ttk.Label(info_frame, text=age, font=font,
                  foreground=love_colors['text'], style='Love.TLabel').grid(
            row=1, column=1, sticky=tk.W, pady=8
        )
        # 性别
        ttk.Label(info_frame, text="性别:", font=font,
                  foreground=love_colors['text'], style='Love.TLabel').grid(
            row=2, column=0, sticky=tk.W, pady=8
        )
        ttk.Label(info_frame, text=gender, font=font,
                  foreground=love_colors['text'], style='Love.TLabel').grid(
            row=2, column=1, sticky=tk.W, pady=8
        )
        # 爱好
        ttk.Label(info_frame, text="爱好:", font=font,
                  foreground=love_colors['text'], style='Love.TLabel').grid(
            row=3, column=0, sticky=tk.NW, pady=8
        )
        ttk.Label(info_frame, text=hobby, font=font, wraplength=200,
                  foreground=love_colors['text'], style='Love.TLabel').grid(
            row=3, column=1, sticky=tk.W, pady=8
        )
        # 分隔线
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=15)
        # 按钮框架
        btn_frame = ttk.Frame(frame, style='Love.TFrame')
        btn_frame.pack(pady=10)
        # 同意按钮

        def on_agree():
            # 按钮点击动画
            agree_btn.config(style='LovePressed.TButton')
            frame.after(100, lambda: agree_btn.config(style='Love.TButton'))
            frame.after(200, lambda: self._handle_choice_result_with_animation(
                pair_window, 1, name, share_key, p, g, q))
        # 不同意按钮

        def on_disagree():
            # 按钮点击动画
            disagree_btn.config(style='LovePressed.TButton')
            frame.after(100, lambda: disagree_btn.config(style='Love.TButton'))
            frame.after(200, lambda: self._handle_choice_result_with_animation(
                pair_window, 0, name, share_key, p, g, q))
        # 创建自定义样式
        style = ttk.Style()
        style.configure('Love.TFrame', background='#FFE4E1')
        style.configure('Love.TLabel', background='#FFE4E1')
        style.configure('Love.TButton', background=love_colors['button'],
                        foreground=love_colors['button_text'], font=font,
                        padding=8, relief='flat', borderwidth=0)
        style.configure('LovePressed.TButton', background=love_colors['button_pressed'],
                        foreground=love_colors['button_text'], font=font,
                        padding=8, relief='flat', borderwidth=0)

        # 创建按钮
        agree_btn = ttk.Button(btn_frame, text="💖 接受 💖", command=on_agree)
        agree_btn.pack(side=tk.LEFT, padx=15)

        disagree_btn = ttk.Button(btn_frame, text="❌ 拒绝 ❌", command=on_disagree)
        disagree_btn.pack(side=tk.LEFT, padx=15)

        # 确保窗口完全渲染后再居中
        pair_window.update_idletasks()
        self.center_window(pair_window)

    def _draw_decorative_hearts(self, canvas):
        """在Canvas上绘制装饰心形"""
        heart_size = 20
        heart_color = '#C71585'

        # 绘制多个心形
        hearts_positions = [(50, 50), (350, 50), (50, 350), (350, 350),
                            (100, 100), (300, 100), (100, 300), (300, 300)]

        for x, y in hearts_positions:
            self._draw_heart(canvas, x, y, heart_size, heart_color)

    def _draw_heart(self, canvas, x, y, size, color):
        """在Canvas上绘制单个心形"""
        # 心形曲线的参数方程
        t = [i / 10 for i in range(0, 63)]  # 0到2π的参数值
        points = []

        for i in t:
            x_coord = 16 * (size / 20) * (math.sin(i) ** 3)
            y_coord = -13 * (size / 20) * math.cos(i) + 5 * (size / 20) * math.cos(2 * i) + \
                      2 * (size / 20) * math.cos(3 * i) + (size / 20) * math.cos(4 * i)
            points.append(x + x_coord)
            points.append(y + y_coord)

        # 绘制心形
        canvas.create_polygon(points, fill=color, outline='')

    def _animate_title(self, label):
        """为标题添加闪烁动画"""
        colors = ['#C71585', '#FF69B4', '#DB7093']
        index = 0

        def update_color():
            nonlocal index
            label.config(foreground=colors[index])
            index = (index + 1) % len(colors)
            label.after(500, update_color)

        update_color()

    def _handle_choice_result_with_animation(self, window, choice, name, share_key, p, g, q):
        """处理选择结果并添加关闭动画"""
        # 淡出动画
        alpha = window.attributes('-alpha')
        if alpha > 0:
            alpha -= 0.1
            window.attributes('-alpha', alpha)
            window.after(50, lambda: self._handle_choice_result_with_animation(
                window, choice, name, share_key, p, g, q))
        else:
            window.destroy()
            self.handle_choice_result(choice, name, share_key, p, g, q)

    def handle_choice_result(self, result, pair_name, share_key,p,g,q):
        # 根据共享密钥得到公钥
        public_key=self.elgamal.generate_public_key(share_key,g,p)
        file_name = f"{self.client.username}_phone_key.txt"
        with open(file_name,"r") as f:
            phone_key_int = int(f.read().strip())
        if result == 1:  # 用户接受
            m = 1
            encrypt_message=self.elgamal.encrypt(m,(p,g,public_key,q))
        else:  # 用户拒绝
            m = self.elgamal.generate_random_message(p, q)
            encrypt_message = self.elgamal.encrypt(m, (p, g, public_key, q))
        # 加密用于电话号码加密的密钥
        encrypt_key = self.elgamal.encrypt(phone_key_int, (p, g, public_key, q))
        # 发送加密后的选择给服务器
        ms = f"choice:{encrypt_message} pair_name:{pair_name} username:{self.client.username} key:{encrypt_key}"
        self.client.send_user_message(ms)
        return

    def handle_pair_no_choice(self,message):
        temp=message[15:].strip()
        ms=f"{temp} 还没选择"
        self.append_message(ms)

    def handle_pair_result(self,message):
        # 从消息中提取c1,c2,匹配用户的姓名，p
        temp = message.split()
        pair_name=temp[1].split(':')[1]
        pair_phone=temp[2].split(':')[1]
        c1 = int(temp[3].split(':')[1])
        c2 = int(temp[4].split(':')[1])
        p= int(temp[5].split(':')[1])
        # 寻找和匹配用户共享的密钥
        identifier=f"{pair_name}:"
        private_way=f"{self.client.username}_share_key.txt"
        found=False
        with open(private_way,"r") as f:
            lines=f.readlines()
            for line in lines:
                line = line.strip()
                # 检查行是否以标识符开头
                if line.startswith(identifier):
                    # 获取标识符后面的部分
                    private_key = int(line[len(identifier):].lstrip())
                    found=True
                    break
                else:
                    continue
        if not found:
            self.append_message("未找到共享密钥")
            return
        # 用找到的共享密钥对密文进行解密
        result=decrypt(c1,c2,p,private_key)
        result_byte=result.to_bytes(16, byteorder='big')
        result_hex = result_byte.hex()
        phone=sm4.sm4_decrypt(result_hex,pair_phone)
        # 结果为数字，双方都选择了接受，匹配成功
        if phone.isdigit():
            self.append_message(f"恭喜你收获爱情！你的有缘人{pair_name} 联系方式是：{phone}")
        # 结果不为数字，匹配失败
        else:
            self.append_message("配对失败，不要气馁，有缘人在后面哦！~")


    def handle_no_more_pair(self):
        """处理无更多配对的情况，停用匹配按钮"""
        self.append_message("当前没有可配对的用户")
        # 停用匹配按钮
        self.match_button.config(state=tk.DISABLED)  # 设置为禁用状态
        # 可选：显示提示信息
        self.status_var.set("已认证: 无更多配对，匹配按钮已禁用")

    def on_closing(self):
        """处理窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出系统吗?"):
            self.client.disconnect()
            self.root.destroy()


class ChatClient:
    """聊天客户端主类"""
    def __init__(self, host='localhost', port=8888, gui=None):
        self.host = host
        self.port = port
        self.client_socket = None
        self.running = False
        self.username = None
        self.authenticated = False
        self.gui = gui
        self.receive_thread = None
        self.server_public_key = None
        self.phone_number = None

    def start(self):
        """启动客户端，建立与服务器的连接并初始化消息接收线程"""
        # 创建TCP套接字（IPv4协议，流式连接）
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.host, self.port)  # 服务器地址元组（IP, 端口）
        # 更新GUI状态（若存在）
        if self.gui:
            self.gui.status_var.set(f"连接到服务器 {server_address}")
        try:
            # 设置连接超时为10秒，避免长时间阻塞
            self.client_socket.settimeout(10)
            # 向服务器发起连接请求
            self.client_socket.connect(server_address)
            # 取消超时设置，后续通信使用默认阻塞模式
            self.client_socket.settimeout(None)
            # 连接成功后的GUI反馈
            if self.gui:
                self.gui.status_var.set("已连接到服务器")
                self.gui.append_message("已连接到服务器")
            self.running = True  # 标记客户端为运行状态
            # 创建并启动消息接收线程
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True  # 设置为守护线程，主线程退出时自动终止
            self.receive_thread.start()  # 启动线程
        except Exception as e:
            # 连接异常处理
            error_msg = f"连接错误: {e}"
            if self.gui:
                self.gui.status_var.set(error_msg)  # GUI显示错误状态
                self.gui.append_message(error_msg)  # GUI添加错误日志
            else:
                print(error_msg)  # 控制台输出错误
        finally:
            # 最终状态检查（无论是否连接成功）
            if not self.running and self.gui:
                self.gui.status_var.set("未连接")  # 连接失败时更新GUI状态

    def receive_messages(self):
        """接收服务器消息的线程函数"""
        try:
            while self.running:
                data = self.client_socket.recv(4096)
                if not data:
                    raise ConnectionResetError("服务器关闭连接")
                message = data.decode('utf-8')
                if message == "AUTH_REQUIRED":  # 处理认证请求
                    self._handle_auth_required()
                elif message.startswith("AUTH_") or message.startswith("REGISTER_"):  # 处理登录或者注册结果
                    self.process_auth_message(message)
                elif message.startswith("PUBLIC_KEY:"):  # 处理来自服务器的公钥
                    # 安全解析公钥
                    public_key_str = message[11:].strip()
                    try:
                        if not (public_key_str.startswith("(") and public_key_str.endswith(")")):
                            raise ValueError("公钥格式错误")
                        params = public_key_str[1:-1].split(",")
                        if len(params) != 4:
                            raise ValueError(f"公钥应包含4个参数，当前收到{len(params)}个")
                        p, g, h,q = map(int, [param.strip() for param in params])
                        public_key_tuple = (p, g, h, q)
                        if self.gui:
                            self.gui.root.after(0, lambda: self.gui.handle_public_key(public_key_tuple))
                    except Exception as e:
                        if self.gui:
                            self.gui.append_message(f"解析公钥出错: {e}")
                elif message == "PUBLIC_KEY_RECEIVED":  # 服务器已接收公钥
                    if self.gui:
                        self.gui.append_message("服务器已接收公钥")
                elif message == "PUBLIC_KEY_ERROR":
                    # 上传的公钥处理失败
                    if self.gui:
                        self.gui.append_message("公钥格式错误，请重新连接")
                elif message.startswith("USER_INFO_REQUEST:") or message.startswith(
                        "USER_INFO_SAVED:") or message.startswith("USER_INFO_ERROR:") or message.startswith(
                    "USER_INFO_EXIST"):
                    # 处理用户个人信息相关消息到GUI处理
                    if self.gui:
                        self.gui.root.after(0, lambda msg=message: self.gui.handle_info_message(msg))
                elif message == "INFO_EXIST":
                    continue
                elif message.startswith("pair_key:"):
                    # 和匹配用户生成共享密钥
                    if self.gui:
                        self.gui.root.after(0, lambda msg=message: self.gui.handle_pair_key_message(msg))
                elif message.startswith("pair_no_choice:"):
                    # 处理匹配的用户还没选择的情况
                    if self.gui:
                        self.gui.root.after(0, lambda msg=message: self.gui.handle_pair_no_choice(msg))
                elif message.startswith("pair_result:"):
                    # 处理匹配结果
                    if self.gui:
                        self.gui.root.after(0, lambda msg=message: self.gui.handle_pair_result(msg))
                elif message.startswith("NO_MORE_PAIR"):
                    # 处理没有匹配用户的情况
                    if self.gui:
                        self.gui.root.after(0, lambda:  self.gui.handle_no_more_pair())
                else:
                    if self.gui:
                        self.gui.append_message(f"收到消息: {message}")
                    else:
                        print(f"收到消息: {message}")
        # 异常处理
        except ConnectionResetError:
            error_msg = "连接被服务器重置"
            self._handle_disconnect(error_msg)
        except OSError as e:
            if self.running:
                error_msg = f"连接错误: {e}"
                self._handle_disconnect(error_msg)
        except Exception as e:
            error_msg = f"接收消息时发生意外错误: {e}"
            self._handle_disconnect(error_msg)

    def _handle_auth_required(self):
        """处理认证请求"""
        if self.gui:
            self.gui.root.after(0, self.gui.show_auth_window)
        else:
            print("需要认证")

    def _handle_disconnect(self, error_msg):
        """处理断开连接的辅助方法"""
        self.disconnect()
        if self.gui:
            self.gui.status_var.set(error_msg)
            self.gui.append_message(error_msg)
        else:
            print(error_msg)

    def process_auth_message(self, message):
        """处理认证相关消息"""
        if message == "AUTH_SUCCESS":
            self.authenticated = True
            if self.gui:
                self.gui.status_var.set(f"已认证: {self.username}")
                self.gui.append_message("认证成功! ")
                self.gui.set_auth_result("AUTH_SUCCESS")
                self.gui.match_button.config(state=tk.NORMAL)
                self.gui.exit_button.config(state=tk.NORMAL)
                # 认证成功后，检查用户信息
                self.send_user_message("info_check")
                return
            else:
                print("认证成功!")
        elif message == "AUTH_FAIL":
            if self.gui:
                self.gui.append_message("认证失败! 用户名或密码错误。")
                self.gui.set_auth_result("认证失败! 用户名或密码错误。")
            else:
                print("认证失败! 用户名或密码错误。")
        elif message == "REGISTER_SUCCESS":
            if self.gui:
                self.gui.append_message("注册成功! 请重新登录。")
                self.gui.set_auth_result("REGISTER_SUCCESS")
            else:
                print("注册成功! 请重新登录。")
        elif message == "REGISTER_FAIL":
            if self.gui:
                self.gui.append_message("注册失败! 用户名已存在。")
                self.gui.set_auth_result("注册失败! 用户名已存在。")
            else:
                print("注册失败! 用户名已存在。")
        elif message == "AUTH_ERROR" or message == "REGISTER_ERROR":
            if self.gui:
                self.gui.append_message("认证/注册格式错误!")
                self.gui.set_auth_result("认证/注册格式错误!")
            else:
                print("认证/注册格式错误!")

    def send_auth_message(self, auth_type, username, password):
        """发送认证消息到服务器"""
        try:
            self.client_socket.sendall(f"{auth_type}_{username}:{password}".encode('utf-8'))
        except Exception as e:
            error_msg = f"发送认证消息时出错: {e}"
            if self.gui:
                self.gui.append_message(error_msg)
                self.gui.set_auth_result(error_msg)
            else:
                print(error_msg)

    def send_user_message(self, message):
        """发送明文消息到服务器"""
        if message.lower() == 'exit':
            self.disconnect()
            return

        if self.running and self.authenticated:
            try:
                self.client_socket.sendall(message.encode('utf-8'))
            except Exception as e:
                error_msg = f"发送消息时出错: {e}"
                if self.gui:
                    self.gui.append_message(error_msg)
                else:
                    print(error_msg)

    def disconnect(self):
        """断开与服务器的连接"""
        self.running = False
        try:
            if self.client_socket:
                self.client_socket.close()
        except Exception as e:
            print(f"关闭socket时出错: {e}")


def main():
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()