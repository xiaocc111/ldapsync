import FileOperation
import requests

config = FileOperation.load_config('config.yaml')
corpid = config['ewechat']['corpid']
corpsecret = config['ewechat']['corpsecret']
department_id = config['ewechat']['department_id']


# 企业微信认证
def get_access_token(corpid, corpsecret):
    config = FileOperation.load_config('config.yaml')
    token_url = config['ewechat']['token_url']
    payload = {
        'corpid': corpid,
        'corpsecret': corpsecret
    }
    response = requests.get(token_url, params=payload)
    if response.ok:
        return response.json().get('access_token')
    else:
        raise Exception('Failed to get access token')


# 获取部门员工信息
def get_department_users(access_token, department_id):
    user_url = f"https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token={access_token}&department_id={department_id}&fetch_child=1"
    response = requests.get(user_url)
    if response.ok:
        return response.json().get('userlist')
    else:
        raise Exception('Failed to get department users')


def result():
    users = get_department_users(get_access_token(corpid, corpsecret), department_id)
    return users


if __name__ == '__main__':
    for user in result():
        print(user)
