import sqlite3

# 连接到数据库
conn = sqlite3.connect('client_information.db')

# 创建游标对象
cursor = conn.cursor()

# 执行SQL查询
cursor.execute("SELECT * FROM users")

# 获取查询结果
result = cursor.fetchall()

# 输出结果
for row in result:
    print(row)

# 关闭连接
cursor.close()
conn.close()