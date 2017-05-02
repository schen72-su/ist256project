#coding=utf-8
import datetime
from pprint import  pprint
from collections import OrderedDict
import requests
import urllib
import sys
from bs4 import BeautifulSoup
import lxml
import csv
import os.path
import time
import random
import threading
import queue
from configparser import ConfigParser
import json

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
DRESS_INDEX = {"Hot":{'man':['shorts','polo man',],'woman':['blose','skirts','polo woman']},
               'Comfort':{'man':['long shirt man'],'woman':['long shirt women']},
               'CoolComfort':{'man':['Knit man'],'woman':['Knit woman']},
               'Cool':{'man':['woollen sweater man','Suits','jacket man'],'woman':['sweater woman','jacket woman']},
               'Cold':{'man':['overcoats man'],'woman':['coats women']},
               'Chill':{'man':['down jacket'],'woman':['coats women']}
}

#下载页面函数
def download(url,i_headers,retries_nums,parm = {}):
    html_doc = ""
    try:
        #url无参数传输
        if len(parm) == 0:
            req = urllib.request.Request(url, headers=i_headers)
        # url有参数传输
        else:
            parms = urllib.parse.urlencode(parm)
            req = urllib.request.Request(url % parms , headers=i_headers)
        response = urllib.request.urlopen(req , None, 50)
        html_doc = response.read()  # 爬取的页面嘛
        wait_seconds()
    except  Exception as  ex:
        print("Download error:",ex)
        if retries_nums > 0 :
            #失败后尝试重新下载
            html_doc = download(url, i_headers, retries_nums - 1,parm)
            wait_seconds()
    return html_doc

#延迟函数
def wait_seconds():
    time.sleep(random.randint(3,5))

#输入位置由google转化为标准坐标
def google_geocode(location):
    i_headers = {'User-Agent': USER_AGENT}
    param = {'address': location,'key':'AIzaSyD5T5xPVxtMhSXvEpZxAV1xSoBJKo3Qbpk'}
    doc = download('https://maps.googleapis.com/maps/api/geocode/json?%s',i_headers,0,param)
    location_dic = json.loads(doc.decode('utf-8'))
    return  location_dic


#返回坐标对应地区的天气情况
def darksky_weather(lat,lng):
    i_headers = {'User-Agent': USER_AGENT}
    url_fmt = 'https://api.darksky.net/forecast/1c17d82398779ffb1166e5dc7e37e885/{lat},{lng}'
    doc = download(url_fmt.format(lat = lat,lng = lng),i_headers,1)
    weather_dic = json.loads(doc.decode('utf-8'))
    return weather_dic


#根据当地天气找到适合的衣着并在本地保存图片
def save_cloth_imgs(type, filename):
    i_headers = {'User-Agent':USER_AGENT,'Host': 'www.hm.com'}
    hm_url = 'http://www.hm.com/us/products/search?%s'
    parms = {'q':type}
    #找到对应衣着的图片集
    doc = download(hm_url,i_headers,1,parms)
    soup = BeautifulSoup(doc, "lxml", from_encoding="utf-8")
    img_divs = soup.find_all(name='li',attrs={'class':'has-secondary-image'})
    human_img_url_list = []
    for div in img_divs:
        # print(str(div.find(name='div',attrs={'class':'image'}).find_all(name='img')[1]['src']))
        human_img_url_list.append("https:" + str(div.find(name='div',attrs={'class':'image'}).find_all(name='img')[1]['src']))
    # 随机挑选一张图片返回其网址
    rand_index = random.randrange(0,(len(human_img_url_list) - 1))

    i_headers2 = {'user-agent': USER_AGENT,'host':'lp.hm.com',
                  }
    #图片保存
    img_url = human_img_url_list[rand_index].replace(' ','+')
    print(img_url)
    img = download(img_url, i_headers2, 2)
    with open(filename, "wb") as f:
        f.write(img)

#华氏度摄氏度转换
def F_to_C(tem):
    return  round((tem - 32)/1.8 ,1)


#根据温度调整衣着
def get_temperature_type(tem_c):
    if tem_c >= 24.0:
        return "Hot"
    elif tem_c > 18 and tem_c <= 24.0:
        return "Comfort"
    elif tem_c > 18.0 and tem_c <= 21.0:
        return 'CoolComfort'
    elif tem_c > 11.0 and tem_c <= 18.0:
        return 'Cool'
    elif tem_c > 6.0 and tem_c <= 11.0:
        return 'Cold'
    else :
        return 'Chil'


def main():
    out_path = r'./out'
    if not os.path.exists(out_path):        os.mkdir(out_path)
    input_A = input("Please input location: ")
    print(input_A)
    location_dic = google_geocode(input_A)
    if location_dic['status'] == 'OK':
        formatted_address = location_dic["results"][0]['formatted_address']
        coord  = location_dic["results"][0]['geometry']['location']

        weather_dic = darksky_weather(coord['lat'],coord['lng'])
        current_weather_dic = weather_dic['currently']

        # pprint(current_weather_dic)
        current_temp = float(current_weather_dic['apparentTemperature'])
        temperature_type = get_temperature_type(F_to_C(current_temp))
        print("The formatted address is ", formatted_address)
        print("The location is ", coord)
        print("The apparent temperature is ",str(current_temp))
        print("The type of temperature is ",temperature_type)

        cloth_type = DRESS_INDEX[temperature_type]
        random_woman_cloth_type = cloth_type['woman'][random.randint(0,(len(cloth_type['woman'])-1))]
        random_man_cloth_type = cloth_type['man'][random.randint(0,(len(cloth_type['man'])-1))]
        print(random_woman_cloth_type)
        print(random_man_cloth_type)

        with open('./out/weather.json','wt',encoding='utf-8')as f:
            json.dump(current_weather_dic,f,ensure_ascii=False,indent=4)
        save_cloth_imgs(random_woman_cloth_type, "./out/woman.jpg")
        save_cloth_imgs(random_man_cloth_type, "./out/man.jpg")
    else:
        print("The location you given can't be recoginzed!")
        return

main()

