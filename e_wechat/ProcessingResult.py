import FileOperation
import csv
import json
import os
from LDAPResult import LDAPManager
from collections import Counter

ldap_manager = LDAPManager('config.yaml')


# 将信息同步到OpenLDAP
def openldap_sync(users):
    csv_file = FileOperation.openldap_csv_file

    # 添加用户到 CSV 文件
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if os.path.exists(FileOperation.openldap_csv_file):
            # 文件存在，清空文件
            with open(FileOperation.openldap_csv_file, 'w', encoding='utf-8') as file:
                file.truncate(0)  # 清空文件内容
        else:
            # 文件不存在，继续执行
            pass
        for user in users:
            mobile_suffix = user["mobile"][-4:]
            # 跳过 status 为 2 的用户
            if user.get('status') == 2:
                continue
            # 检查两个邮箱字段，如果为空，则使用 biz_mail 字段
            if user["email"] == '':
                user["email"] = user["biz_mail"]
            new_row = [
                FileOperation.to_pinyin(user["name"]) + mobile_suffix,
                FileOperation.generate_random_password(),
                user["name"],
                user["email"],
                user["position"],
                user["mobile"]
            ]
            writer.writerow(new_row)

    ldap_manager.sync_users_from_csv(csv_file)


# 生成群晖LDAP导入的csv文件，并使用逗号分隔符
def synology_csv_create(users):
    # 临时文件名
    temp_csv_file = FileOperation.csv_file + '.tmp'
    repetitive__csv_file = FileOperation.repetitive_csv_file

    # 添加用户到临时 CSV 文件
    with open(temp_csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for user in users:
            # 检查两个邮箱字段，如果为空，则使用 biz_mail 字段
            if user["email"] == '':
                user["email"] = user["biz_mail"]
            new_row = [
                FileOperation.to_pinyin(user["name"]),
                FileOperation.generate_random_password(),
                user["name"],
                user["email"],
                '',
                '',
                user["position"],
                '',
                user["mobile"],
                user["mobile"],
                user["mobile"],
                '',
                '',
                ''
            ]
            writer.writerow(new_row)

    # 读取临时 CSV 文件
    with open(temp_csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)

    # 提取拼音列
    pinyin_column = [row[0] for row in rows]

    # 计算拼音重复次数
    pinyin_count = Counter(pinyin_column)

    # 找出重复的拼音
    duplicate_pinyin = {pinyin for pinyin, count in pinyin_count.items() if count > 1}

    # 过滤掉重复的用户
    filtered_rows = [row for row in rows if row[0] not in duplicate_pinyin]

    # 找出被删除的用户
    deleted_users = [row for row in rows if row[0] in duplicate_pinyin]

    # 将被删除的用户添加到新的 CSV 文件中，并在拼音字段后面加上 mobile 的后四位字符
    with open(repetitive__csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for user in deleted_users:
            mobile_suffix = user[8][-4:]  # 获取 mobile 的后四位字符
            modified_pinyin = f"{user[0]}{mobile_suffix}"  # 修改拼音字段
            modified_row = [modified_pinyin] + user[1:]
            writer.writerow(modified_row)

    # 删除临时文件
    import os
    os.remove(temp_csv_file)

    # 将过滤后的用户写回原 CSV 文件
    with open(FileOperation.csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(filtered_rows)

    # 打印删除的用户
    for user in deleted_users:
        print(f"排除重复用户: {user}")


# 查看所有用户
def display_users(users):
    users_json = json.dumps(users, indent=4, ensure_ascii=False)
    return users_json


# 查看用户关键信息
def display_user_key_information(users):
    all_num = 0
    on_duty_num = 0
    resigned_num = 0
    for user in users:
        all_num += 1
        if user["status"] == 2:
            resigned_num += 1
        else:
            on_duty_num += 1
        # 检查两个邮箱字段
        if user["email"] == '':
            user["email"] = user["biz_mail"]
        elif user["email"] != '' and user["email"] != user["biz_mail"]:
            print(
                "******************员工" + user["name"] + "用户邮箱设置有问题，两个邮箱分别为：" + user["email"] + '和' +
                user["biz_mail"] + "******************")
            continue
        print(
            user["name"] +
            ';' +
            user["position"] +
            ';' +
            user["mobile"] +
            ';' +
            user["email"] +
            ';' +
            str(user["status"])
        )
    print("共查询到 " + str(all_num) + " 个用户")
    print("在职员工 " + str(on_duty_num) + " 人")
    print("离职员工 " + str(resigned_num) + " 人")


# def search_employee_status(users):
#     # 获取企业微信用户和LDAP用户并转换成json格式
#     ewchat_userlist = json.loads(display_users(users))


# 查看离职员工手机号
def search_departing_employees_num(users):
    filtered_difference = set()
    # 获取企业微信用户和LDAP用户并转换成json格式
    ewchat_userlist = json.loads(display_users(users))
    ldap_userlist = json.loads(ldap_manager.get_ldap_user_json())

    # 提取出企业微信用户的手机号并转换成合集
    ewechat_mobile = [user.get('mobile') for user in ewchat_userlist]
    ewechat_mobile = set(ewechat_mobile)
    # print(type(ewechat_mobile))

    # 提出LDAP用户的手机号并转换成合集
    ldap_mobile = [user.get('telephoneNumber') for user in ldap_userlist]
    ldap_mobile = set(ldap_mobile)
    # print(type(ldap_mobile))
    difference = ldap_mobile - ewechat_mobile

    # 过滤掉空字符串 ''
    filtered_difference = {mobile for mobile in difference if mobile != ''}
    # 企业微信中状态为2的也是离职员工
    for resigned_user in ewchat_userlist:
        if resigned_user.get('status') == 2:
            mobile = resigned_user.get('mobile')
            if mobile and mobile != '':
                filtered_difference.add(mobile)

    #print("企业微信中的离职员工:", filtered_difference)
    return filtered_difference


# 检查是否有重复的中文名
def check_difference(users):
    ewchat_userlist = json.loads(display_users(users))
    ewechat_mobile = [user.get('name') for user in ewchat_userlist]
    if len(ewechat_mobile) != len(set(ewechat_mobile)):
        print("存在重复的 name 值")
        # 找出重复的 mobile 值
        from collections import Counter
        duplicates = [mobile for mobile, count in Counter(ewechat_mobile).items() if count > 1]
        print("重复的 name 值:", duplicates)
    else:
        print("没有重复的 name 值")
