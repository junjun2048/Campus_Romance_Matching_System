from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
import os
import binascii


def generate_key():
  random_key = os.urandom(16)
  return random_key

def sm4_encrypt(key, plaintext):
    crypt_sm4 = CryptSM4()
    crypt_sm4.set_key(key, SM4_ENCRYPT)
    if isinstance(plaintext, str):
        plaintext = plaintext.encode('utf-8')
    encrypt_value = crypt_sm4.crypt_ecb(plaintext) # ECB模式
    return binascii.hexlify(encrypt_value).decode()


def sm4_decrypt(key_hex, ciphertext_hex):
    # 将十六进制密钥和密文转为bytes
    key_bytes = binascii.unhexlify(key_hex)
    ciphertext_bytes = binascii.unhexlify(ciphertext_hex)

    # 初始化SM4解密
    crypt_sm4 = CryptSM4()
    crypt_sm4.set_key(key_bytes, SM4_DECRYPT)

    # ECB模式解密
    plaintext_bytes = crypt_sm4.crypt_ecb(ciphertext_bytes)

    # 尝试解码为字符串（和加密时的encode('utf-8')对应）
    try:
        return plaintext_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return plaintext_bytes  # 如果是二进制数据直接返回bytes

