# -*- coding:utf-8 -*-
"""电子科技大学登陆模块"""
import requests
from .exceptions import LoginError
import re


def __get_mid_text(text, left_text, right_text, start=0):
    """获取中间文本"""
    left = text.find(left_text, start)
    if left == -1:
        return ('', -1)
    left += len(left_text)
    right = text.find(right_text, left)
    if right == -1:
        return ('', -1)
    return (text[left:right], right)


def login(num, password):
    """登陆并返回一个requests模块的session"""
    url = 'http://idas.uestc.edu.cn/authserver/login?service='
    # 获取lt,execution
    new_session = requests.session()
    new_session.cookies.clear()
    response = new_session.get(url)

    lt_data, end = __get_mid_text(response.text, '"lt" value="', '"')
    if end == -1:
        raise LoginError('登录信息获取失败')

    execution, end = __get_mid_text(
        response.text, '"execution" value="', '"', end)
    # 构造表格
    postdata = {
        'username': num,
        'password': password,
        'lt': lt_data,
        'dllt': 'userNamePasswordLogin',
        'execution': execution,
        '_eventId': 'submit',
        'rmShown': '1'
    }
    response = new_session.post(url, data=postdata)
    name = "Unknow"
    if "auth_username" in response.text:
        name = re.search('auth_username.*?</span>', response.text, re.DOTALL).group(0)
        name = re.search('<span>(.*)', name, re.DOTALL).group(1)
        name = re.search('<span>(.*)</span>', name, re.DOTALL).group(1).replace('\t', '').replace('\n', '').replace(' ', '')
    if '密码有误' in response.text:
        print('密码错误')
        return 201

    elif '验证码' in response.text:
        return 202

    response = new_session.get(
        'http://eams.uestc.edu.cn/eams/courseTableForStd.action')
    if '踢出' in response.text:
        click_url = __get_mid_text(response.text, '请<a href="', '"')
        new_session.get(click_url[0])

    return {"session": new_session, "name": name}
