from Crypto.Util.number import getPrime, getRandomRange, GCD, isPrime
import pickle
import base64


class ElGamal:
    def __init__(self, key_length=512):
            self.key_length = key_length
            self.public_key = None
            self.private_key = None

    def generate_parameter(self):
        #生成q,p,g
        while True:
            q = getPrime(self.key_length-1)
            p = 2 * q + 1
            if is_Prime(p):
                break
        # 找到模p阶为q的生成元g
        g=self.find_generator(p,q)
        return p, g, q

    def is_generator(self,g, p, q):
        return pow(g, 2, p) != 1 and pow(g, q, p) != 1

    def find_generator(self,p, q):
        # 先测试常见小候选
        for g_candidate in [2, 3, 5, 6, 7, 10, 11, 12]:
            if self.is_generator(g_candidate, p, q):
                return g_candidate
        # 随机搜索（概率极高）
        while True:
            g = getRandomRange(2, p - 2)
            if self.is_generator(g, p, q):
                return g

    def generate_private_key(self, q):
        temp=getRandomRange(1, q - 1)
        return temp

    def generate_public_key(self, private_key, g, p):
        temp=pow(g, private_key, p)
        return temp

    def generate_random_message(self, p, q):
        # 生成随机的明文
        temp = getRandomRange(1, p - 1)

        return temp

    def encrypt(self, plaintext, public_key=None):
        if public_key is None:
            if self.public_key is None:
                raise ValueError("未提供公钥")
            public_key = self.public_key

        p, g, h, q = public_key

        if isinstance(plaintext, int):
            m = plaintext
            # 将字符串转换为整数
        elif isinstance(plaintext, str):
            m = int.from_bytes(plaintext.encode(), byteorder='big')
            # 将字节转换为整数
        elif isinstance(plaintext, bytes):
            m = int.from_bytes(plaintext, byteorder='big')
        else:
            raise TypeError("明文必须是整数、字符串或字节类型")

        # 确保消息小于p
        if m >= p:
            raise ValueError(f"消息过大，必须小于 {p}")

        # 选择随机数k
        while True:
            k = getRandomRange(2, q - 2)
            if GCD(k, p - 1) == 1:
                break
        # 计算密文组件
        c1 = pow(g, k, p)
        c2 = (m * pow(h, k, p)) % p
        # 将密文元组转换为Base64字符串
        ciphertext_tuple = (c1, c2)
        ciphertext_bytes = pickle.dumps(ciphertext_tuple)
        ciphertext_base64 = base64.b64encode(ciphertext_bytes).decode('utf-8')
        return ciphertext_base64


def homomorphic_multiplication_and_pow(pair_choice, choice,p,phone_key):
    # 同态乘法和同态幂运算
    # 将两个选择密文分解成两个密文元组
    ciphertext1_bytes = base64.b64decode(choice.encode('utf-8'))
    ciphertext1_tuple = pickle.loads(ciphertext1_bytes)
    ciphertext2_bytes = base64.b64decode(pair_choice.encode('utf-8'))
    ciphertext2_tuple = pickle.loads(ciphertext2_bytes)
    c1,c2=ciphertext1_tuple
    c1_pair,c2_pair=ciphertext2_tuple
    # 随机选取随机数r
    r=getRandomRange(2,p-1)
    # c*c_pair 是同态乘法，再进行r次幂计算，最后模p
    c1_new=pow(c1*c1_pair,r,p)
    c2_new=pow(c2*c2_pair,r,p)
    # 电话号码和选择密文同态乘法
    phone_key_bytes = base64.b64decode(phone_key.encode('utf-8'))
    phone_key_tuple = pickle.loads(phone_key_bytes)
    c1_phone_key,c2_phone_key=phone_key_tuple
    c1_new=pow(c1_new*c1_phone_key,1,p)
    c2_new = pow(c2_new * c2_phone_key, 1, p)
    return c1_new, c2_new


def decrypt(c1,c2, p,private_key=None):
    if private_key is None:
        raise ValueError("未提供私钥")
    a = private_key
    # 计算共享密钥
    s = pow(c1, a, p)
    # 计算明文
    m = (c2 * pow(s, p - 2, p)) % p  # 使用费马小定理计算s的模逆
    return m


def is_Prime(n, k=5):

    # 处理小素数和小数
    if n < 2:
        return False
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
        if n % p == 0:
            return n == p

    # 预计算 n-1 = d*2^s
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    # 优化的测试基数 (对于64位以上数足够可靠)
    test_bases = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]

    for a in test_bases[:k]:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True
