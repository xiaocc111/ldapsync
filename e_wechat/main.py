import FileOperation
import ProcessingResult
import ewechat_auth
from LDAPResult import LDAPManager

username_list = []
ldap_manager = LDAPManager('config.yaml')

message = ("\n/*******/分割线/*******/\n"
           "请输入序号（输入 q 退出程序）：\n"
           "1.生成群晖LDAP导入所需的CSV文件；\n"
           "2.直接在控制台查看所有用户信息（企业微信）；\n"
           "3.只查看所有用户的关键信息和统计总数（名字、职位、手机号、邮箱）\n"
           "4.查询离职员工（根据手机号）\n"
           "5.删除离职员工（根据手机号）\n"
           "6.查看公司重名的人\n"
           "7.在OpenLDAP添加企业微信用户\n"
           "请输入：")


# 主程序
# def main(corpid, corpsecret, department_id, user_select):
# access_token = ewechat_auth.get_access_token(corpid, corpsecret)
# users = ProcessingResult.get_department_users(access_token, department_id)
def main(selection, users):
    if selection == 1:
        FileOperation.init_script()
        ProcessingResult.synology_csv_create(users)
    elif selection == 2:
        print(ProcessingResult.display_users(users))
    elif selection == 3:
        ProcessingResult.display_user_key_information(users)
    elif selection == 4:
        telephone_list = ProcessingResult.search_departing_employees_num(users)
        ldap_manager.search_departing_employees(telephone_list)
    elif selection == 5:
        telephone_list = ProcessingResult.search_departing_employees_num(users)
        ldap_manager.delete_departing_employees(telephone_list)
    elif selection == 6:
        ProcessingResult.check_difference(users)
    elif selection == 7:
        ProcessingResult.openldap_sync(users)
    else:
        # ProcessingResult.display_user_key_information(users)
        print("\n请输入正确数字！\n")
    #return username_list


if __name__ == '__main__':
    while True:
        try:
            user_input = input(message)
            if user_input.lower() == 'q':
                print("程序已退出")
                break
            user_input = int(user_input)
            print("你输入的是:", user_input)
            user_select = user_input
            main(user_select, ewechat_auth.result())
        except ValueError:
            print("\n请输入数字或 q 退出程序!!\n")
    # user_input = int(input(message))
    # print("你输入的是:", user_input)
    # user_select = user_input
    # main(user_select, ewechat_auth.result())

    # main(user_select, ewechat_auth.result())
    # main(corpid, corpsecret, department_id, user_select)
    # print(main(corpid, corpsecret, department_id))
