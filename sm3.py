from gmssl import sm3, func


def derive_elgamal_private_key(shared_secret, q):
    # 将共享密钥转换为字节
    shared_secret_bytes = shared_secret.to_bytes((shared_secret.bit_length() + 7) // 8, 'big')
    # 调用SM3算法生成哈希值
    shared_secret_list = func.bytes_to_list(shared_secret_bytes)  # 转换为字节列表
    sm3_hash_hex = sm3.sm3_hash(shared_secret_list)  # 计算SM3哈希值
    # 从哈希值派生私钥
    derived_key = int(sm3_hash_hex, 16)
    final_key = derived_key % (q - 2) + 1
    return final_key


def generate_sm3_hash(data):
    # 处理不同类型的输入
    if isinstance(data, int):
        data_bytes = data.to_bytes((data.bit_length() + 7) // 8, 'big')
    elif isinstance(data, str):
        data_bytes = data.encode('utf-8')
    elif isinstance(data, bytes):
        data_bytes = data
    else:
        raise TypeError("输入数据类型必须为int/str/bytes")

    # 转换为字节列表并计算SM3哈希
    data_list = func.bytes_to_list(data_bytes)
    hash_hex = sm3.sm3_hash(data_list)
    return hash_hex
