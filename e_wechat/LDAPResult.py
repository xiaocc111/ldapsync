import json
import csv
import FileOperation
from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE
from concurrent.futures import ThreadPoolExecutor, as_completed


class LDAPManager:
    def __init__(self, config_path):
        # 配置 LDAP 服务器信息
        self.config = FileOperation.load_config(config_path)
        self.ldap_server = self.config['ldap']['ldap_server']
        self.ldap_user = self.config['ldap']['ldap_user']
        self.ldap_password = self.config['ldap']['ldap_password']
        self.base_dn = self.config['ldap']['base_dn']
        self.server = Server(self.ldap_server, get_info=ALL)

    # 创建 LDAP 服务器对象
    def _connect(self):
        return Connection(self.server, user=self.ldap_user, password=self.ldap_password, auto_bind=True)

    # 获取用户
    def get_ldap_users_demo(self):
        conn = self._connect()

        # 搜索所有用户
        search_filter = '(objectClass=person)'  # 可以根据需要调整搜索过滤器
        attributes = ['cn', 'uid', 'mail']  # 可以根据需要调整需要获取的属性

        conn.search(self.base_dn, search_filter, search_scope=SUBTREE, attributes=attributes)

        # 打印搜索结果
        for entry in conn.entries:
            print(entry)

        conn.unbind()

    def get_ldap_user_json(self):
        conn = self._connect()

        # 搜索所有用户
        search_filter = '(objectClass=person)'  # 可以根据需要调整搜索过滤器
        attributes = ['cn', 'mail', 'telephoneNumber', 'gecos']  # 需要获取的属性

        conn.search(self.base_dn, search_filter, search_scope=SUBTREE, attributes=attributes)

        # 将搜索结果转换成 JSON 格式
        users = []
        for entry in conn.entries:
            user = {
                'gecos': entry.gecos.value if entry.gecos else None,
                'cn': entry.cn.value if entry.cn else None,
                'mail': entry.mail.value if entry.mail else None,
                'telephoneNumber': entry.telephoneNumber.value if entry.telephoneNumber else ''
            }
            users.append(user)

        # 将用户列表转换成 JSON 字符串
        users_json = json.dumps(users, indent=4, ensure_ascii=False)
        conn.unbind()
        return users_json

    # 查询离职员工信息
    def search_departing_employees(self, telephone_list):
        conn = self._connect()
        results = []

        for telephone_number in telephone_list:
            search_filter = f'(telephoneNumber={telephone_number})'
            conn.search(search_base=self.base_dn, search_filter=search_filter, search_scope=SUBTREE,
                        attributes=['cn', 'mail', 'gecos', 'telephoneNumber'])

            for entry in conn.entries:
                result = {
                    'cn': entry.cn.value if entry.cn else None,
                    'mail': entry.mail.value if entry.mail else None,
                    'gecos': entry.gecos.value if entry.gecos else None,
                    'telephoneNumber': entry.telephoneNumber.value if entry.telephoneNumber else ''
                }
                results.append(result)

        results_json = json.dumps(results, indent=4, ensure_ascii=False)
        if results_json == '[]':
            print("\nLDAP中未找到离职员工\n")
        else:
            print("\nLDAP中的离职员工：\n")
            print(results_json)
        conn.unbind()

    # 删除离职员工信息
    def delete_departing_employees(self, phone_list):
        conn = self._connect()
        for telephone_number in phone_list:
            search_filter = f'(telephoneNumber={telephone_number})'
            conn.search(search_base=self.base_dn, search_filter=search_filter, search_scope=SUBTREE)

            for entry in conn.entries:
                try:
                    conn.delete(entry.entry_dn)
                    print(f"已删除 {entry.entry_dn}")
                except Exception as e:
                    print(f"删除 {entry.entry_dn} 失败: {e}")

        conn.unbind()

    # 找到所有没写电话号码的LDAP用户
    def get_users_with_empty_telephone_number(self):
        conn = self._connect()
        search_filter = '(&(objectClass=person)(!(telephoneNumber=*)))'
        conn.search(search_base=self.base_dn, search_filter=search_filter, search_scope=SUBTREE,
                    attributes=['cn', 'mail', 'telephoneNumber'])

        users = []
        for entry in conn.entries:
            user = {
                'cn': entry.cn.value,
                'mail': entry.mail.value if entry.mail else None,
                'telephoneNumber': entry.telephoneNumber.value if entry.telephoneNumber else None
            }
            users.append(user)

        for user in users:
            print(user)

        conn.unbind()

    def sync_users_from_csv(self, csv_file_path):
        """
        从 CSV 文件中同步用户到 OpenLDAP

        :param csv_file_path: CSV 文件路径
        """
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            users = []
            for row in reader:
                username, password, display_name, email, employee_type, mobile = row
                user_dn = f"cn={username},cn=users,{self.base_dn}"
                user_info = {
                    'cn': username,
                    'sn': username,
                    'uid': username,
                    'userPassword': password,
                    'displayName': display_name,
                    'mail': email,
                    'employeeType': employee_type,
                    'mobile': mobile
                }
                users.append((user_dn, user_info))

        # 使用多线程同步用户
        success_count = 0
        failure_count = 0
        failed_users = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.add_user, user_dn, user_info): (user_dn, user_info) for user_dn, user_info in users}
            for future in as_completed(futures):
                user_dn, user_info = futures[future]
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                        print(f"已同步用户 {user_dn} 到 LDAP")
                    else:
                        failure_count += 1
                        failed_users.append(user_dn)
                        print(f"用户 {user_dn} 同步失败: {result}")
                except Exception as e:
                    failure_count += 1
                    failed_users.append(user_dn)
                    print(f"发生错误: {e}")

        # 打印总结信息
        print(f"同步完成，成功同步的用户数量: {success_count}")
        print(f"失败的用户数量: {failure_count}")
        if failed_users:
            print("失败的用户cn列表:")
            for user in failed_users:
                print(f"  - {user}")

    def add_user(self, user_dn, user_info):
        """
        在 OpenLDAP 中添加一个用户

        :param user_dn: 用户的 DN (Distinguished Name)
        :param user_info: 用户信息字典，例如 {'cn': 'John Doe', 'sn': 'Doe', 'mail': 'john.doe@example.com'}
        """
        try:
            # 连接到 LDAP 服务器
            conn = self._connect()

            # 准备用户数据
            attributes = {
                'objectClass': ['top', 'person', 'organizationalPerson', 'inetOrgPerson'],
                **user_info
            }

            # 执行添加操作
            result = conn.add(user_dn, attributes=attributes)

            if result:
                return True
            else:
                return False

            # 关闭连接
            #conn.unbind()
        except Exception as e:
            return str(e)


if __name__ == '__main__':
    ldap_manager = LDAPManager('config.yaml')
    # print(ldap_manager.get_ldap_user_json())
    # telephone_list = ['123456789']
    # ldap_manager.delete_departing_employees(telephone_list)
    #ldap_manager.get_users_with_empty_telephone_number()
    # user_dn = "cn=John Doe,cn=users,dc=test,dc=cn"
    # user_info = {
    #     'cn': 'John Doe',
    #     'sn': 'Doe',
    #     'mail': 'john.doe@example.com',
    #     'uid': 'johndoe',
    #     'displayName': '中文',
    #     'userPassword': '{SSHA}hashed_password'  # 假设密码已经哈希处理
    # }
    # ldap_manager.add_user(user_dn, user_info)
    ldap_manager.sync_users_from_csv('openldap.csv')
