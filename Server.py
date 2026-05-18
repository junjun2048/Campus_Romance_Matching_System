import socket
import threading
import time
import os
from ElGamal import *
from data import *


class ClientHandler:
    """处理单个客户端连接"""

    def __init__(self, client_socket, client_address, server):
        self.client_socket = client_socket
        self.client_address = client_address
        self.server = server
        self.active = True
        self.username = None
        self.authenticated = False
        self.receive_thread = None
        self.client_public_key = None
        self.user_info_request = False
        self.user_info_save=False
        self.public_key_exchanged = False
        self.had_push =[]

    def start(self):
        """启动客户端处理线程"""
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        print(f"已连接客户端: {self.client_address}")
        self.send_message("AUTH_REQUIRED")

    def receive_messages(self):
        """接收客户端消息的线程函数"""
        try:
            while self.active:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                if not self.authenticated:
                    # 未认证状态，处理认证
                    self.handle_authentication(message)
                elif message.startswith("info_check"):
                    if not self.user_info_request and not self.check_user_in_database(self.username):
                        # 已认证但未收集用户信息，请求用户信息
                        self.request_user_information()
                        self.user_info_request = True
                    else:
                        self.send_message("INFO_EXIST")
                elif self.user_info_request and message.startswith("USER_INFO:"):
                    # 处理用户提交的信息
                    self.handle_user_information(message)
                    self.user_info_request = False
                    self.user_info_save=True
                elif not self.public_key_exchanged and self.user_info_save:
                    # 用户信息已收集，处理公钥交换
                    if message.startswith("CLIENT_PUBKEY:"):
                        self.handle_client_public_key(message)
                        self.public_key_exchanged = True
                        print(f"{self.username} 公钥交换完成")
                        self.send_message("PUBLIC_KEY_RECEIVED")
                    else:
                        # 发送服务器公钥并请求客户端公钥
                        self.send_message(f"PUBLIC_KEY:{self.server.public_key}")
                        print(f"已发送服务器公钥给 {self.username}")
                elif message == "PUSH_REQUEST":
                    # 客户端请求匹配用户
                    self.handle_push(self.username)
                elif message.startswith("choice:"):
                    # 接收用户的选择
                    self.handle_choice(message)
                else:
                    # 正常处理消息
                    print(f"来自 {self.username}: {message}")
                    self.server.broadcast(f"[{self.username}] {message}", self)

        except Exception as e:
            print(f"处理客户端 {self.client_address} 时出错: {e}")
        finally:
            # 无论是否异常，均调用disconnect方法
            self.disconnect()

    def handle_choice(self, message):
        temp = message.split()
        choice = temp[0].split(':')[1]
        pair_username = get_username_by_name(temp[1].split(':')[1])
        user_name=temp[2].split(':')[1]
        self_phone_key=temp[3].split(':')[1]
        pair_phone_key=None
        key1 = f"({pair_username},{user_name})"
        key2 = f"({user_name},{pair_username})"
        pair_choice = None
        try:
            # 1. 以读写模式打开文件，读取全部内容
            with open("client_choice.txt", "r+") as f:
                lines = f.readlines()  # 读取所有行
                f.seek(0)  # 关键：回到文件开头
                f.truncate()  # 关键：清空文件内容
                pair_choice = None
                key_found = False
                for line in lines:
                    stripped_line = line.strip()
                    # 查找匹配的key2
                    if not key_found and key2 in stripped_line and ':' in stripped_line:
                        # 提取冒号后的内容作为pair_choice
                        pair_part = stripped_line.split(key2 + ":", 1)[1]  # 分割出key2后的部分
                        pair_choice = pair_part.split("phone_key:")[0].strip()  # 提取phone_key前的内容
                        # 提取phone_key（phone_key冒号后的内容）
                        phone_part = stripped_line.split("phone_key:", 1)
                        if len(phone_part) > 1:
                            pair_phone_key = phone_part[1].strip()
                        key_found = True
                        break
                    else:
                        # 其他行原样写回
                        f.write(line)
                if not key_found:
                    f.write(f"{key1}: {choice} phone_key:{self_phone_key}\n")
        except FileNotFoundError:
            # 文件不存在时创建新文件并写入
            with open("client_choice.txt", "w") as f:
                f.write(f"{key1}: {choice} phone_key:{self_phone_key}\n")
        # 5. 发送消息
        if pair_choice is None:
            pair_person = get_person_by_username(pair_username)
            print(1)
            self.send_message(f"pair_no_choice:{pair_person['name']}")
        else:
            self.handle_pair_choice(pair_choice, choice,pair_username,pair_phone_key,self_phone_key)
            print(2)

    def handle_pair_choice(self,pair_choice, choice,pair_username,pair_phone_key,self_phone_key):
        # 将两个选择密文进行同态乘法
        p=self.server.public_key[0]
        print(f"pair_choice:{pair_choice} choice:{choice}")
        c1, c2 = homomorphic_multiplication_and_pow(pair_choice, choice,p,pair_phone_key)
        pair_name=get_name_by_username(pair_username)
        pair_phone=get_phone_by_username(pair_username)
        ms = f"pair_result: pair_name:{pair_name} pair_phone:{pair_phone} c1:{c1} c2:{c2} p:{self.server.public_key[0]}"
        self.send_message(ms)
        # 将当前用户的联系方式密钥的密文进行同态乘法，并保存
        c1_new,c2_new=homomorphic_multiplication_and_pow(pair_choice, choice,p,self_phone_key)
        ms2=f"({pair_username},{self.username}): c1:{c1_new} c2:{c2_new} \n"
        with open("choice_result.txt", "w") as f:
            f.write(ms2)

    def find_had_pair(self, username):
        # 查找是否有被推送的记录
        try:
            with open("client_choice.txt", "r") as f:  # 只读模式打开
                file_content = f.readlines()  # 读取所有行
            # 检查每一行
                for line in file_content:
                    line = line.strip()  # 去除首尾空白
                    if line.startswith(f"({username},"):
                        pos_start = line.find(f"({username},") + len(f"({username},")
                        pos_end = line.find(")", pos_start)
                        if pos_end == -1:
                            return None, False  # 格式不正确
                    pos2 = line[pos_start:pos_end].strip()
                    self.had_push.append(pos2)
                    return pos2, True  # 返回配对用户和选择
            # 没有找到匹配行
            return None, False
        except FileNotFoundError:
            return None, False  # 文件不存在
        except Exception as e:
            print(f"查找配对时出错: {e}")
            return None, False

    def find_pair_result(self,username):
        # 查找是否存在已经得到最终结果的情况
        found=False
        try:
            with open("choice_result.txt", "r+") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith(f"({username},"):
                        pos_start = line.find(f"({username},") + len(f"({username},")
                        pos_end = line.find(")", pos_start)
                        if pos_end == -1:
                            return False
                        c1_pos = line.find("c1:")
                        c2_pos = line.find("c2:")
                        c1=line[c1_pos + 3:].split()[0]
                        c2=line[c2_pos + 3:].split()[0]
                        pair_username = line[pos_start:pos_end].strip()
                        pair_name = get_name_by_username(pair_username)
                        self.had_push.append(pair_username)
                        get_phone_by_username(pair_name)
                        pair_username = get_username_by_name(pair_name)
                        pair_phone = get_phone_by_username(pair_username)
                        ms = f"pair_result: pair_name:{pair_name} pair_phone:{pair_phone} c1:{c1} c2:{c2} p:{self.server.public_key[0]}"
                        self.send_message(ms)
                        return True
            if not found:
                return False
        except FileNotFoundError:
            return False

    def handle_push(self, username):
        # 数据库只有1个用户
        if get_user_count()==1:
            self.send_message("NO_MORE_PAIR")
            return
        if self.find_pair_result(username):  # 查找是否有之前的匹配结果
            return
        pair_username=None
        pair_person=None
        found = False
        pair_username,result=self.find_had_pair(username)  # 双向推送
        if result:
            pair_person=get_person_by_username(pair_username)
            found=True
        else:
            # 随机匹配一个
            a = get_opposite_gender_count(username)
            for _ in range(a):
                pair_person = pair(username)
                if not pair_person:
                    print(f"未找到与 {username} 配对的用户")
                    self.send_message("ERROR: 未找到配对用户")
                    return
                pair_username = pair_person['username']
                if pair_username not in self.had_push:
                    self.had_push.append(pair_username)
                    print(f"已推送用户: {pair_username}")
                    print(f"已推送列表: {self.had_push}")
                    found = True  # 标记已找到
                    break
        # 循环结束后检查是否找到
        if not found:
            print("没有更多可推送的配对用户")
            self.send_message("NO_MORE_PAIR")
            return
        print(f"配对用户: {pair_username}")
        # 获取配对用户的公钥
        pair_public_key = self.server.get_client_public_key(str(pair_username))
        # 发送匹配信息
        self.send_message(f"pair_key:{pair_public_key} p:{self.server.public_key[0]} q:{self.server.public_key[3]} "
                          f"g:{self.server.public_key[1]} "
                          f"pair_name:{pair_person['name']} pair_gender:{pair_person['gender']} "
                          f"pair_age:{pair_person['age']} pair_hobby:{pair_person['hobby']}")
        if pair_public_key is None:
            print(f"用户 {pair_username} 的公钥不存在")
            self.send_message("ERROR: 配对用户公钥不存在")
            return

    def handle_user_information(self, message):
        """处理客户端提交的用户信息"""
        try:
            info = message[10:].strip()
            name, age, gender, hobby, phone = info.split(',')

            # 调用服务器方法保存用户信息
            success = self.server.save_user_information(self.username, name, int(age), gender, hobby,phone)
            if success:
                self.send_message("USER_INFO_SAVED:您的信息已成功保存")
                print(f"已保存用户 {self.username} 的信息")
                # 保存成功后，请求客户端公钥
                self.send_message(f"PUBLIC_KEY:{self.server.public_key}")
                print(f"已发送服务器公钥给 {self.username}")
            else:
                self.send_message("USER_INFO_ERROR:信息保存失败，请重新提供")
        except Exception as e:
            print(f"处理用户信息时出错: {e}")
            self.send_message("USER_INFO_ERROR:信息格式错误，请使用格式(姓名,年龄,性别,邮箱)")

    def handle_client_public_key(self, message):
        """处理客户端公钥"""
        if message.startswith("CLIENT_PUBKEY:"):
            try:
                public_key = int(message[14:].strip())
                self.client_public_key = public_key
                print(f"收到客户端 {self.username} 的公钥: {public_key}")
                # 保存到数据库
                self.server.add_client_public_key(self.username, public_key)
            except Exception as e:
                print(f"解析客户端公钥出错: {e}")
                self.send_message("PUBLIC_KEY_ERROR")

    def handle_authentication(self, message):
        """处理客户端认证"""
        if message.startswith("AUTH_"):
            auth_data = message[5:].split(':')
            if len(auth_data) == 2:
                username, password = auth_data
                if self.server.authenticate_user(username, password):
                    self.username = username
                    self.authenticated = True
                    self.send_message("AUTH_SUCCESS")
                    print(f"用户 '{self.username}' 已认证")
                else:
                    self.send_message("AUTH_FAIL")
                    print(f"用户 '{username}' 认证失败")
            else:
                self.send_message("AUTH_ERROR")
        elif message.startswith("REGISTER_"):
            reg_data = message[9:].split(':')
            if len(reg_data) == 2:
                username, password = reg_data
                if self.server.register_user(username, password):
                    self.send_message("REGISTER_SUCCESS")
                    print(f"用户 '{username}' 注册成功")
                else:
                    self.send_message("REGISTER_FAIL")
                    print(f"用户 '{username}' 注册失败")
            else:
                self.send_message("REGISTER_ERROR")
        else:
            self.send_message("AUTH_REQUIRED")

    def check_user_in_database(self, username):
        """检查数据库中是否存在用户信息"""
        return self.server.check_user_in_database(username)

    def request_user_information(self):
        """向客户端请求用户基本信息"""
        request_msg = "USER_INFO_REQUEST:请提供您的基本信息(格式:姓名,年龄,性别,邮箱)"
        self.send_message(request_msg)
        print(f"已向用户 {self.username} 请求基本信息")

    def send_message(self, message):
        """向客户端发送消息"""
        try:
            if self.active:
                self.client_socket.sendall(message.encode('utf-8'))
                return True
            return False
        except Exception as e:
            print(f"向客户端 {self.client_address} 发送消息时出错: {e}")
            self.disconnect()
            return False

    def disconnect(self):
        """断开客户端连接"""
        if self.active:
            self.active = False
            self.client_socket.close()
            self.server.remove_client(self)
            username_info = f"{self.username} " if self.username else ""
            print(f"客户端 {username_info}({self.client_address}) 已断开连接")


class UserManager:
    """用户管理类"""
    def __init__(self, file_path="account.txt"):
        self.file_path = file_path
        self.users = {}
        self.load_users()
    def load_users(self):
        """从文件加载用户"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            username, password = line.split(':', 1)
                            self.users[username] = password
                print(f"已加载 {len(self.users)} 个用户")
            except Exception as e:
                print(f"加载用户时出错: {e}")

    def save_users(self):
        """保存用户到文件"""
        try:
            with open(self.file_path, 'w') as f:
                for username, password in self.users.items():
                    f.write(f"{username}:{password}\n")
            print(f"已保存 {len(self.users)} 个用户")
        except Exception as e:
            print(f"保存用户时出错: {e}")

    def authenticate_user(self, username, password):
        """验证用户"""
        if username in self.users:
            return self.users[username] == password
        return False

    def register_user(self, username, password):
        """注册用户"""
        if username in self.users:
            return False
        self.users[username] = password
        self.save_users()
        return True


class ChatServer:
    """聊天服务器主类"""

    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False
        self.elgamal = ElGamal()
        self.public_key = None
        self.private_key = None
        self.user_manager = UserManager()

    def start(self):
        """启动服务器"""
        # 创建TCP套接字
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置套接字选项，允许地址重用，避免服务器重启时的地址占用问题
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = (self.host, self.port)
        print(f"启动服务器 {server_address}")
        # 绑定套接字到指定地址和端口
        self.server_socket.bind(server_address)
        # 开始监听连接，最大等待队列长度为5
        self.server_socket.listen(5)
        print("服务器正在监听连接...")
        self.running = True
        # 检查数据库是否存在，不存在则初始化
        if not check_database_exists("client_information.db"):
            init_db()
            print("数据库初始化完成")
        # 生成参数
        p, g, q = self.elgamal.generate_parameter()
        # 生成私钥
        self.elgamal.private_key = self.elgamal.generate_private_key(q)
        # 生成公钥
        y = self.elgamal.generate_public_key(self.elgamal.private_key, g, p)  # 服务器公钥y = g^a mod p
        self.public_key = (p, g, y, q)
        # 创建并启动连接处理线程
        self.connection_thread = threading.Thread(target=self.handle_connections)
        # 设置为守护线程，主线程退出时自动终止
        self.connection_thread.daemon = True
        self.connection_thread.start()
        # 主线程负责处理用户输入
        self.handle_user_input()

    def handle_connections(self):
        """处理新的客户端连接，通过循环持续监听并分配处理器"""
        while self.running:  # 当服务器运行标志为True时持续循环
            try:
                # 阻塞等待客户端连接，返回客户端套接字和地址
                client_socket, client_address = self.server_socket.accept()
                # 创建客户端处理器实例，传入套接字、地址和服务器自身引用
                client_handler = ClientHandler(client_socket, client_address, self)
                # 启动客户端处理器线程
                client_handler.start()
                # 将处理器添加到客户端列表，便于统一管理
                self.clients.append(client_handler)
            except Exception as e:  # 捕获连接处理过程中的异常
                if self.running:  # 仅在服务器未停止时打印错误
                    print(f"接受连接时出错: {e}")
                time.sleep(1)  # 异常后暂停1秒，避免频繁报错

    def remove_client(self, client_handler):
        """从客户端列表中移除客户端"""
        if client_handler in self.clients:
            self.clients.remove(client_handler)

    def broadcast(self, message, exclude_client=None):
        """向所有客户端广播消息"""
        for client in self.clients:
            if client != exclude_client and client.authenticated:
                client.send_message(message)

    def handle_user_input(self):
        """处理服务器管理员输入"""
        try:
            while self.running:
                print("\n===== 服务器控制台 =====")
                print("命令:")
                print("  list - 显示在线客户端")
                print("  send <id> <message> - 向特定客户端发送消息")
                print("  broadcast <message> - 向所有客户端广播消息")
                print("  shutdown - 关闭服务器")
                print("======================\n")
                command = input("输入命令: ")
                if command.lower() == 'shutdown':
                    self.shutdown()
                    break
                elif command.lower() == 'list':
                    self.list_clients()
                elif command.startswith('send '):
                    parts = command.split(' ', 2)
                    if len(parts) == 3:
                        client_id = int(parts[1]) - 1
                        message = parts[2]
                        self.send_to_client(client_id, message)
                    else:
                        print("命令格式: send <id> <message>")
                elif command.startswith('broadcast '):
                    message = command[10:]
                    self.broadcast(message)
                else:
                    print("未知命令")
        except KeyboardInterrupt:
            self.shutdown()

    def list_clients(self):
        """列出所有在线客户端"""
        print("\n在线客户端:")
        if not self.clients:
            print("  没有客户端连接")
        else:
            for i, client in enumerate(self.clients):
                auth_status = "已认证" if client.authenticated else "未认证"
                info_status = "信息已完善" if client.check_user_in_database(client.username) else "信息未完善"
                pubkey_status = "公钥已交换" if client.public_key_exchanged else "公钥未交换"
                username_info = f"{client.username} " if client.username else ""
                print(f"  [{i + 1}] {username_info}({client.client_address}) - {auth_status}, {info_status}, {pubkey_status}")
        print()

    def send_to_client(self, client_id, message):
        """向特定客户端发送消息"""
        try:
            if 0 <= client_id < len(self.clients):
                client = self.clients[client_id]
                if client.send_message(message):
                    username_info = f"{client.username} " if client.username else ""
                    print(f"已发送消息到客户端 {username_info}({client.client_address})")
                else:
                    print(f"无法发送消息到客户端 {client.client_address}")
            else:
                print("客户端ID无效")
        except ValueError:
            print("客户端ID必须是数字")

    def authenticate_user(self, username, password):
        """验证用户"""
        return self.user_manager.authenticate_user(username, password)

    def register_user(self, username, password):
        """注册用户"""
        return self.user_manager.register_user(username, password)

    def shutdown(self):
        """关闭服务器"""
        print("正在关闭服务器...")
        self.running = False
        for client in self.clients:
            client.disconnect()
        self.clients.clear()
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("服务器已关闭")

    def has_client_public_key(self, username):
        """检查数据库中是否存在用户公钥"""
        try:
            with sqlite3.connect('client_information.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT public_key FROM users WHERE username = ?", (username,)
                )
                result = cursor.fetchone()
                return result is not None and result[0] is not None
        except Exception as e:
            print(f"检查公钥时出错: {e}")
            return False

    def add_client_public_key(self, username, public_key):
        """将客户端公钥保存到数据库"""
        try:
            with sqlite3.connect('client_information.db') as conn:
                cursor = conn.cursor()
                # 将公钥转换为字符串存储
                cursor.execute(
                    "UPDATE users SET public_key = ? WHERE username = ?",
                    (str(public_key), username)
                )
                if cursor.rowcount == 0:
                    print(f"用户 {username} 不存在，无法保存公钥")
                    return False
            print(f"已保存客户端 {username} 的公钥到数据库")
            return True
        except Exception as e:
            print(f"保存客户端公钥时出错: {e}")
            return False


    def get_client_public_key(self, username):
        """从数据库获取指定用户的公钥"""
        try:
            public_keys = load_client_public_keys()
            return public_keys.get(username)
        except Exception as e:
            print(f"获取用户 {username} 公钥时出错: {e}")
            return None

    def check_user_in_database(self, username):
        """检查数据库中是否存在用户信息"""
        try:
            with sqlite3.connect('client_information.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"查询用户 {username} 信息时数据库错误: {e}")
            return False
        except Exception as e:
            print(f"查询用户信息时发生意外错误: {e}")
            return False

    def save_user_information(self, username, name, age, gender, hobby,phone):
        """保存用户信息到数据库"""
        try:
            return add_user(username, name, age, gender, hobby,phone)
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: users.name" in str(e):
                print(f"用户 {name} 已存在，无法重复保存")
                return False
            else:
                print(f"保存用户信息时发生唯一约束错误: {e}")
                return False
        except sqlite3.Error as e:
            print(f"保存用户信息时数据库错误: {e}")
            return False
        except Exception as e:
            print(f"保存用户信息时发生意外错误: {e}")
            return False


if __name__ == "__main__":
    server = ChatServer()
    server.start()
