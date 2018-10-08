# -*- coding: utf-8 -*-
from re import compile
from requests import get
from bs4 import BeautifulSoup
from hashlib import md5

TRANSLATER_ADDR = "http://api.fanyi.baidu.com/api/trans/vip/translate"
JSON = {'from': 'auto',
        'to': 'auto',
        'appid': '20180822000197576',
        'salt': '3'}
        
zhPattern = compile('[\u4e00-\u9fa5]+')

def check_language(text):
    if zhPattern.search(text):
        return 1
    return 2

def translate(text):
    try:
        JSON['q'] = text.encode('utf-8')
    except:
        return text
    string = str(JSON['appid']) + str(JSON['q']) + str(JSON['salt']) + '5Ag7XogguSMXVF7tQKfr'
    JSON['sign'] = md5(string.encode('utf-8')).hexdigest()
    res = get(TRANSLATER_ADDR, JSON).json()
    return res['trans_result'][0]['dst']

if __name__ == '__main__':

    while True:
        print(translate(input('What you want to say?')))
