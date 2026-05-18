import sqlite3


def init_db():
    """初始化数据库，创建表结构和自定义函数"""
    with sqlite3.connect('client_information.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL UNIQUE,
                      name TEXT NOT NULL UNIQUE, 
                      age INTEGER,
                      gender TEXT,
                      hobby TEXT,
                      phone TEXT UNIQUE, 
                      public_key TEXT, 
                      register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')


def add_user(username, name, age, gender, hobby, phone=None, public_key=None):
    """添加用户"""
    try:
        with sqlite3.connect('client_information.db') as conn:
            if public_key is not None and phone is not None:
                # 插入包含电话号码和公钥的记录
                conn.execute("""
                    INSERT INTO users (username, name, age, gender, hobby, phone, public_key) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (username, name, age, gender, hobby, phone, str(public_key)))
            elif phone is not None:
                # 插入包含电话号码但不含公钥的记录
                conn.execute("""
                    INSERT INTO users (username, name, age, gender, hobby, phone) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, name, age, gender, hobby, phone))
            elif public_key is not None:
                # 插入包含公钥但不含电话号码的记录
                conn.execute("""
                    INSERT INTO users (username, name, age, gender, hobby, public_key) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, name, age, gender, hobby, str(public_key)))
            else:
                # 插入不包含电话号码和公钥的记录
                conn.execute("""
                    INSERT INTO users (username, name, age, gender, hobby) 
                    VALUES (?, ?, ?, ?, ?)
                """, (username, name, age, gender, hobby))
        return True
    except sqlite3.IntegrityError as e:
        print(f"添加用户时出错: {e}")
        return False




def get_username_by_name(name):
    """通过真实姓名查找用户名"""
    try:
        with sqlite3.connect('client_information.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE name = ?", (name,))
            row = cursor.fetchone()
            return row['username'] if row else None
    except Exception as e:
        print(f"通过姓名查找用户名时出错: {e}")
        return None


def get_name_by_username(username):
    """按用户名查询用户"""
    try:
        with sqlite3.connect('client_information.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return row['name'] if row else None
    except Exception as e:
        print(f"按用户名查询用户时出错: {e}")
        return None


def get_phone_by_username(username):
    """按用户名查询用户"""
    try:
        with sqlite3.connect('client_information.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return row['phone'] if row else None
    except Exception as e:
        print(f"按用户名查询用户时出错: {e}")
        return None

def get_person_by_username(username):
    """按用户名查询用户"""
    try:
        with sqlite3.connect('client_information.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"按用户名查询用户时出错: {e}")
        return None


def get_person_by_name(name):
    """按用户名查询用户"""
    try:
        with sqlite3.connect('client_information.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"按用户名查询用户时出错: {e}")
        return None

def check_database_exists(database_name):
    try:
        connection = sqlite3.connect(database_name)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        if len(tables) > 0:
            return True
        else:
            return False
    except sqlite3.Error as error:
        return False


def pair(username, return_all=False):
    try:
        # 打开数据库，查找可以与用户匹配的用户
        with sqlite3.connect('client_information.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # 获取当前用户信息
            cursor.execute("SELECT gender, age FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                print(f"用户 {username} 不存在")
                return []
            user_gender = user['gender']
            user_age = user['age']
            # 得到和当前用户的相反性别
            opposite_gender = '女' if user_gender == '男' else '男'
            # 计算年龄范围（±5岁）
            age_min = user_age - 5 if user_age else 0
            age_max = user_age + 5 if user_age else 150
            # 构建查询条件
            conditions = ["gender = ?", "username != ?"]
            params = [opposite_gender, username]
            # 添加年龄条件
            if user_age is not None:
                conditions.append("age BETWEEN ? AND ?")
                params.extend([age_min, age_max])
            # 构建SQL查询
            query = """
                SELECT username, name, gender, age, hobby
                FROM users
                WHERE {}
                ORDER BY RANDOM()
            """.format(" AND ".join(conditions))
            # 根据return_all参数设置LIMIT
            if not return_all:
                query += " LIMIT 1"
            # 执行查询
            cursor.execute(query, params)
            users = cursor.fetchall()
            return dict(users[0]) if users else None
    except Exception as e:
        print(f"查找配对用户时出错: {e}")
        return []


def get_user_count():
    """获取数据库中的用户总数"""
    try:
        with sqlite3.connect('client_information.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            return count
    except Exception as e:
        print(f"获取用户数量时出错: {e}")
        return 0


def get_opposite_gender_count(username):
    """获取与指定用户性别相反的用户数量"""
    try:
        with sqlite3.connect('client_information.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 获取指定用户的性别
            cursor.execute("SELECT gender FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                print(f"用户 {username} 不存在")
                return 0

            user_gender = user['gender']
            opposite_gender = '女' if user_gender == '男' else '男'

            # 统计相反性别的用户数量
            cursor.execute("SELECT COUNT(*) FROM users WHERE gender = ? AND username != ?",
                           (opposite_gender, username))
            count = cursor.fetchone()[0]
            return count
    except Exception as e:
        print(f"获取相反性别用户数量时出错: {e}")
        return 0


def load_client_public_keys():
    # 从数据库加载所有客户端公钥
    public_keys = {}
    try:
        with sqlite3.connect('client_information.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, public_key FROM users WHERE public_key IS NOT NULL")
            results = cursor.fetchall()
            for username, key_str in results:
                public_keys[username] = int(key_str)  # 将字符串转换回整数
            print(f"已从数据库加载 {len(public_keys)} 个客户端公钥")
    except Exception as e:
        print(f"从数据库加载公钥时出错: {e}")
    return public_keys
