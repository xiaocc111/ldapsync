import csv
import datetime
import random
import string
import yaml

from pypinyin import pinyin, Style

formatted_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_file = f"{formatted_time}.csv"
repetitive_csv_file = f"repetitive_{formatted_time}.csv"

openldap_csv_file = "openldap.csv"


# 读取配置文件
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


# 中文转换成拼音
def to_pinyin(text, style=Style.NORMAL):
    return ''.join([i[0] for i in pinyin(text, style=style)])


# 生成随机密码
def generate_random_password(length=20):
    # 确保首字符是大写英文
    first_char = random.choice(string.ascii_uppercase)

    # 定义要排除的特殊字符
    # excluded_special_chars = ',、./\\'
    # 定义特殊字符只能包含
    special_characters = "!@#$%&"

    # 字符集，包括字母（大写和小写）、数字以及除了排除字符以外的特殊字符或只能包含的特殊字符
    # special_characters = ''.join(char for char in string.punctuation if char not in excluded_special_chars)
    characters = string.ascii_letters + string.digits + special_characters

    # 生成剩余部分的随机密码
    remaining_password = ''.join(random.choice(characters) for _ in range(length - 1))

    # 确保密码中包含至少一个符合条件的特殊字符
    if not any(char in special_characters for char in remaining_password):
        # 如果没有，则替换密码中的某个随机字符为特殊字符
        insert_index = random.randint(0, length - 2)  # 在剩余密码中随机选择一个位置
        remaining_password = (
                remaining_password[:insert_index] +
                random.choice(special_characters) +
                remaining_password[insert_index + 1:]
        )

    # 组合首字符和剩余部分
    password = first_char + remaining_password

    return password


# 生成csv文件
def init_script():
    # 打开文件以写入数据（如果文件不存在，则会被创建）
    new_row = ['名称', '密码', '描述', '电子邮件', '员工编号', '部门', '员工类型', '标题', '工作电话', '家庭电话',
               '移动电话', '地址', '生日', '群组名称']
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(new_row)
