from json.decoder import JSONDecodeError
import requests as r
import json
import re
import logging
import sys

logging.basicConfig(
  level = logging.INFO,
  format = '%(asctime)s %(levelname)s %(message)s',
  datefmt = '%Y-%m-%dT%H:%M:%S')

class InvalidException(Exception):
    pass

class Sign():
    def __init__(self, cookie):
        if type(cookie) is not str:
            raise TypeError("cookie must be str")
        self.cookie = cookie
        self.headers = {
            'User-Agent': 'okhttp/4.8.0',
            'Cookie' : self.cookie
        }
        self.signin_url = "https://api-takumi.mihoyo.com/common/euthenia/sign"
        self.get_cookie_token_url = "https://api-takumi.mihoyo.com/auth/api/getCookieAccountInfoBySToken?stoken={}&uid={}"
        self.get_token_url = "https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket?login_ticket={}&token_types={}&uid={}"
        self.get_role_url = "https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie?game_biz=bh3_cn"
        self.login_ticket = ""
        self.login_uid = ""
        self.s_token = ""
        self.cookie_token = ""
        

        self.signin_data_templete = {
            "act_id":"e202104072769",
            "region":"",
            "uid":""
        }
        self.bh3_roles = []

    def check_cookie(self):
        # login_ticket 不是必要的
        self.login_ticket = self.get_cookie_by_name("login_ticket")
        self.login_uid = self.get_cookie_by_name("login_uid")
        if self.login_uid == '' or self.login_ticket == '':
            raise InvalidException("cookie 不完整")
        if self.get_cookie_by_name("cookie_token") == '':
            self.get_cookie_token()
        
    
    def get_cookie_token(self):
        if self.s_token == '':
            self.get_s_token()
        url = self.get_cookie_token_url.format(self.s_token,self.login_uid)
        h = r.get(url,headers=self.headers)
        json_data = h.json()
        if json_data['retcode'] == 0:
            self.cookie_token = json_data['data']['cookie_token']
            logging.info("获取cookie_token: " + self.cookie_token)
        else:
            raise InvalidException("登录态失效")
        # 将cookie_token放在cookie中
        self.cookie += (";cookie_token=" + self.cookie_token)

    
    def get_cookie_by_name(self, name):
        pattern = name + "=(.*?);"
        c = re.findall(pattern,self.cookie)
        data = c[0] if len(c) > 0 else ""
        logging.debug("从cookie中获取"+ name + ": " + data)
        return data

    def get_s_token(self):
        self.s_token = self.get_token("1")
        logging.info("获取s_token: " + self.s_token)

    def get_token(self,type):
        url = self.get_token_url.format(self.login_ticket,type,self.login_uid)
        h = r.get(url,headers=self.headers)
        json_data = h.json()
        if json_data['retcode'] == 0:
            return json_data['data']['list'][0]['token']
        else:
            raise InvalidException("登录态失效")

    def get_bh3_roles(self):
        h = r.get(self.get_role_url,headers=self.headers)
        json_data = h.json()
        if json_data['retcode'] == 0:
            role_templete = {'uid':'','region':''}
            for role in json_data['data']['list']:
                new_role = role_templete.copy()
                new_role['uid'] = role['game_uid']
                new_role['region'] = role['region']
                self.bh3_roles.append(new_role)
        else:
            raise InvalidException("登录态失效")
    
    def signin(self,role):
        if type(role) is not dict:
            logging.error("role must be dict")
            return False
        if role['uid'] == '' or role['region'] == '':
            logging.error("role uid or region is empty")
            return False
        signin_data = self.signin_data_templete.copy()
        signin_data['uid'] = role['uid']
        signin_data['region'] = role['region']
        headers = self.headers.copy()
        headers['Referer'] = 'https://webstatic.mihoyo.com/bh3/event/euthenia/index.html?bbs_presentation_style=fullscreen&bbs_game_role_required=bh3_cn&bbs_auth_required=true&act_id=e202104072769&utm_source=bbs&utm_medium=mys&utm_campaign=icon'
        headers['x-rpc-device_id'] = '40bcca52-56e8-3124-b465-20ddc2334c26'
        h = r.post(self.signin_url,headers=headers,data=json.dumps(signin_data))
        json_data = h.json()
        retcode = json_data['retcode']
        hide_uid = "*"*(len(role['uid'])-4) + role['uid'][-4:]
        if retcode == -5003 or retcode == 0:
            logging.info("用户 " + hide_uid + " 签到成功或已经签到")
            return True
        else:
            logging.error("用户 " + hide_uid + " 签到失败")
            logging.error("错误信息: " + json_data['message'])
            return False
    
    def run(self):
        try:
            self.check_cookie()
        except Exception as e:
            logging.error(e)
            exit(-1)
        self.get_bh3_roles()
        if not self.bh3_roles:
            logging.info("没有找到游戏角色")
            exit(-1)
        
        for role in self.bh3_roles:
            if not self.signin(role):
                # 提醒
                pass


if __name__ == "__main__":
    cookies = sys.argv[1]
    for cookie in cookies.split("#"):
        sign = Sign(cookie)
        sign.run()
        

